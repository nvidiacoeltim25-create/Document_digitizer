import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fastapi.staticfiles import StaticFiles
from utils.core_features import clearAllEmailsUtil, compareChequesUtil, compareFaceSignUtil, deleteAttachmentsUtil, deleteEmailsUtil, extractCustomTabularDataUtil, extractDataUtil, fetchEmailUtil, generateEmailGeneralUtil, generateEmailSchemaUtil, getAllFilesInfoUtil, getAllFilesZipUtil, getConfigUtil, getFilesByIdUtil, getReferenceDocsUtil, getSavedDataUtil, mcpChatUtil, saveDataUtil, sendEmailUtil, updateConfigUtil, uploadFilesUtil, verifyUtil


import uuid
from fastapi import FastAPI, UploadFile, File, HTTPException
import uvicorn
import json
from PIL import Image
from fastapi.openapi.docs import get_swagger_ui_html, get_redoc_html

import pymongo
from typing import List

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import httpx
from fastapi import HTTPException
from typing import List
import time

from utils.constants import EMAIL_FETCH_BASEURL, FACE_SIGN_COMPARE_BASEURL, INVOKE_URL_NVIDIA, MCP_PORT, MODELS, NVIDIA_KEY, NVIDIA_MODEL, NVIDIA_MODEL_LLAMA4, PLATFORM, PLATFORMS, PORT, HUGGINGFACE_KEY, config_file_path, attachments_folder

from models.models import AttachmentIDs, ChatRequest, Config, CustomExtractModel, FetchEmailRequest, GeneralEmailInput, Response, Compare, CompareChequesRequest, CompareModel, EmailIDs, EmailRequest, ExtractModel, JsonList, ObjectIDs, Response, SaveDataModel


# Create a folder for attachments if it doesn't exist

os.makedirs(attachments_folder, exist_ok=True)

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["email_database"]
attachments_collection = db["attachments"]
emails_collection = db["emails"]
extractions_collection = db["extractions_collection"]
reference_documents_collection = db["reference_documents"]
cheques_collection = db["cheques_collection"]
tabular_custom_fields_coll = db["tabular_custom_fields_coll"]




# app = FastAPI(openapi_url="/openapi.json")
app = FastAPI(
    )

origins = [
    '*'
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount the 'artifacts_violation' directory
app.mount("/attachments_db", StaticFiles(directory="attachments_db"), name="attachments_db")

# Custom route for Swagger UI
@app.get("/docs", include_in_schema=False)
async def custom_swagger_ui_html():
    return get_swagger_ui_html(openapi_url="/openapi.json", title="Custom API Docs")

# Custom route for ReDoc
@app.get("/redoc", include_in_schema=False)
async def redoc_html():
    return get_redoc_html(openapi_url="/openapi.json", title="Custom API Docs")





# Endpoint to get the current configuration
@app.get("/config", response_model=Config, tags=["admin"])
async def get_config():
    ress = await getConfigUtil()
    return ress

# Endpoint to update the configuration
@app.put("/config", response_model=Config, tags=["admin"])
async def update_config(new_config: Config):
    ress = await updateConfigUtil(new_config)
    return ress


@app.post("/upload/", tags=["DATABASE"])
async def upload_files(files: List[UploadFile] = File(...)):
    ress = await uploadFilesUtil(files)
    # ress = await uploadFilesUtil_ingest(files)
    return ress

# # THIS GIVES METADATA AND FILEPATHS OF MULTIPLE FILES(NO DOWNLOAD LINK)


# THIS WILL RETURN A ZIP CONTAINING ALL REQUSTED FILES
# SEQUNCE WILL BE PRSERVED AS THE LIST OF OBJECT IDS
@app.post("/get_files_by_id/", tags=["DATABASE"])
async def get_files(object_ids: ObjectIDs):
    ress = await getFilesByIdUtil(object_ids)
    return ress

@app.post("/get_all_files_zip/", tags=["DATABASE"])
async def get_files():
    ress = await getAllFilesZipUtil()
    return ress
    
@app.post("/get_all_files_info/", tags=["DATABASE"])
async def get_files():
    ress = await getAllFilesInfoUtil()
    return ress

# Pydantic model for the document


@app.get("/get_refernce_docs", tags=["DATABASE"])
async def get_documents():
    ress = getReferenceDocsUtil()
    return ress


# # API TO IDENTIFY THE TYPE OF DOCUMENT
# @app.post("/get_document_type/", tags=["LLM"])
# async def get_document_type(object_id: str):

#     response = await getDocumentTypeUtil()
#     return response


@app.delete("/delete_attachments/", tags=["delete"])
async def delete_attachments(attachments: AttachmentIDs):
    ress = await deleteAttachmentsUtil(attachments)
    return ress

@app.delete("/delete_emails/", tags=["delete"])
async def delete_emails(email_ids: EmailIDs):
    ress = await deleteEmailsUtil(email_ids)
    return ress

@app.delete("/clear_emails", tags=["delete"])
async def clear_collection():
    ress = await clearAllEmailsUtil()
    return ress

# platforms: nvidia, huggingface
@app.post("/extract_data/", tags=["LLM"])
async def extract_data(extract_model: ExtractModel):
    ress = await extractDataUtil(extract_model)
    return ress
    
@app.post("/extract_custom_tabular/")
async def extract_data(custom_extract_model: CustomExtractModel):
    ress = await extractCustomTabularDataUtil(custom_extract_model)
    return ress
    
# Endpoint to generate consolidated email
@app.post("/generate_email/", tags=["LLM"])
async def generate_email(json_inputs: JsonList):
    ress = await generateEmailSchemaUtil(json_inputs)
    return ress

@app.post("/generate_email_general/", tags=["LLM"])
async def generate_email_general(ge_input: GeneralEmailInput):
    ress = await generateEmailGeneralUtil(ge_input)
    return ress

@app.post("/send-email/",tags=["EMAIL"])
async def send_email_endpoint(email: EmailRequest):
    ress = await sendEmailUtil(email)
    return ress


@app.post("/compare_cheques/", tags=["LLM"])
async def compare_cheques_endpoint(request: CompareChequesRequest):
    ress = await compareChequesUtil(request)
    return ress


# Signature comparison and shareholder certificate verification
@app.post("/verify/", tags=["LLM"])
async def verify(compare: Compare):
    ress = await verifyUtil(compare)
    return ress

@app.post("/fetch_emails", tags=["EMAIL"])
async def forward_chat(fetch_email_model: FetchEmailRequest):
    ress = await fetchEmailUtil(fetch_email_model)
    return ress


@app.post("/save_data", tags=["DATABASE"])
async def save_data(item: SaveDataModel):
    ress = await saveDataUtil(item)
    return ress


@app.get("/get_saved_data/{data_id}", tags=["DATABASE"])
async def get_saved_data(data_id: str):
    ress = await getSavedDataUtil(data_id)
    return ress

# MCP CHAT API
@app.post("/chat", response_model=Response ,tags=["MCP"])
async def forward_chat(request: ChatRequest):
    ress = await mcpChatUtil(request)
    return ress


@app.post("/compare_face_sign_ML", tags=["ML"])
async def compare_face_sign_ML(compare_model: CompareModel):
    ress = await compareFaceSignUtil(compare_model)
    return ress


# DO NOT CHANGE THE PORTS
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=PORT)
