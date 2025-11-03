import os
from rag_pipeline import embed_nvidia, ensure_collection, embed_fallback
from loguru import logger
from typing import List
import requests
from pymilvus import MilvusClient
from dotenv import load_dotenv

load_dotenv()

NVIDIA_API_KEY = os.environ["NVIDIA_API_KEY"]

# ---------- Logging ----------
logger.remove()  # Remove default logger
logger.add("app.log", 
           rotation="1 MB",     
           retention="10 days", 
           level="INFO", 
           enqueue=True,        # Thread-safe logging
           backtrace=True,      # Show full traceback
           diagnose=True)       # Show variable values in tracebacks

logger.info("Application started")

# ---------- Milvus ----------
MILVUS_DB = "/home/sneha-ltim/abrav/Document_Digitizer_backend/RAG_/milvus_rag.db"
COLLECTION = "rag_documents"
DIM = 1024
milvus = MilvusClient(uri=MILVUS_DB)

# ---------- RETRIEVAL ----------
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
        return response
    except Exception as e:
        logger.error(f"LLM request failed: {e}")
        return f"LLM error: {e}"

# ---------- MAIN ----------
if __name__ == "__main__":
    logger.info("Ensuring Milvus collection exists")
    ensure_collection()


    while True:
        user_query = input("Enter your query (or 'exit' to quit): ").strip()
        if user_query.lower() == 'exit':
            logger.info("Exiting application")
            break

        logger.info(f"Running chatbot for user query: {user_query}")
        answer = rag_chatbot(user_query)
        print(f"\nQ: {user_query}")
        print(f"A: {answer}\n")

    # queries = ["Who signed the document?"]
    # for q in queries:
        # logger.info(f"Running chatbot for query: {use}")
        # print(f"\nQ: {q}")
        # print(f"A: {rag_chatbot(q)}")