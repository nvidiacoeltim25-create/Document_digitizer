from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from rag_pipeline import embed_nvidia, ensure_collection, embed_fallback
from loguru import logger
from typing import List
import requests
import os
from pymilvus import MilvusClient
from dotenv import load_dotenv

# Load environment variables
load_dotenv()
NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]

# ---------- Logging ----------
logger.remove()
logger.add("rag_app.log", 
           rotation="1 MB",     
           retention="10 days", 
           level="INFO", 
           enqueue=True,        
           backtrace=True,      
           diagnose=True)

logger.info("FastAPI app starting")

# ---------- Milvus ----------
MILVUS_DB = "/home/sneha-ltim/abrav/Document_Digitizer_backend/RAG_/milvus_rag.db"
COLLECTION = "rag_documents"
DIM = 1024
milvus = MilvusClient(uri=MILVUS_DB)

# ---------- FastAPI Setup ----------
app = FastAPI()
origins = [
    # "http://localhost",
    # "http://localhost:8001",
    # Add more origins as needed
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------- Input Model ----------
class QueryInput(BaseModel):
    query: str

# ---------- Retrieval ----------
def retrieve(query: str, top_k: int = 5) -> List[str]:
    logger.info(f"Retrieving context for query: {query}")
    try:
        q_emb = embed_nvidia([query])[0]
    except Exception as e:
        logger.warning(f"NVIDIA embedding failed: {e}. Using fallback.")
        q_emb = embed_fallback([query])[0]

    try:
        hits = milvus.search(
            collection_name=COLLECTION,
            data=[q_emb],
            limit=top_k,
            output_fields=["text"],
        )[0]
        results = [h.entity.get("text") for h in hits]
        logger.info(f"Retrieved {len(results)} results")
        return results
    except Exception as e:
        logger.error(f"Milvus search failed: {e}")
        return []

# ---------- RAG Chatbot ----------
def rag_chatbot(query: str) -> str:
    logger.info(f"Processing query: {query}")
    ctx = retrieve(query)
    if not ctx:
        logger.warning("No relevant context found.")
        return "No relevant info."

    prompt = f"Context:\n{' '.join(ctx)}\n\nQuestion: {query}\nAnswer:"
    try:
        r = requests.post(
            "https://integrate.api.nvidia.com/v1/chat/completions", 
            json={
                "model": "nvidia/llama-3.1-nemotron-nano-vl-8b-v1", 
                "messages": [{"role": "user", "content": prompt}],
                "max_tokens": 300,
                "temperature": 0.7,
            },
            headers={"Authorization": f"Bearer {NVIDIA_API_KEY}"},
            timeout=120,
        )
        r.raise_for_status()
        response = r.json()["choices"][0]["message"]["content"]
        logger.info("LLM response received successfully")
        logger.info(f"Returning response from logic fn as : {type(response)}")
        logger.info(f"Response content from logic fn: {response}")
        return response
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return f"LLM error: {e}"

# ---------- Endpoint ----------
import json 

@app.post("/rag-chatbot")
async def rag_chatbot_endpoint(data: QueryInput):
    logger.info("Received request at /rag-chatbot endpoint")
    try:
        logger.info(f"Received query: {data.query}")
        response = rag_chatbot(data.query)
        logger.info(f"Returning response from endpoint as : {type(response)}")
        logger.info(f"Response content: {response}")
        r = {'response': response}  
        return json.dumps(r)
    
    except Exception as e:
        logger.error(f"Error in endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# # ---------- Startup ----------
# @app.on_event("startup")
# def startup_event():
#     logger.info("Ensuring Milvus collection exists")
#     ensure_collection()

# DO NOT CHANGE THE PORTS
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8006)