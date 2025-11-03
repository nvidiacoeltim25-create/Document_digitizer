# import pymongo
# import base64
# import io
# import zipfile
# import os
# import requests

# # MongoDB connection
# client = pymongo.MongoClient("mongodb://localhost:27017/")
# db = client["email_database"]
# emails_collection = db["emails"]

# # Function to decode and extract ZIP
# def decode_and_extract_zip(base64_string, output_folder="extracted_attachments"):
#     zip_data = base64.b64decode(base64_string)
#     zip_buffer = io.BytesIO(zip_data)
#     with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
#         os.makedirs(output_folder, exist_ok=True)
#         zip_ref.extractall(output_folder)
#         return zip_ref.namelist()

# # Function to upload files
# def upload_files(file_paths):
#     files = [('files', (os.path.basename(path), open(path, 'rb'))) for path in file_paths]
#     response = requests.post("http://localhost:8003/upload/", files=files)
#     if response.status_code == 200:
#         return response.json().get("uploaded_files", [])
#     else:
#         print("Upload failed:", response.text)
#         return []

# # Simulated API response
# api_response = [
#     {
#         "email_id": "u351720@gmail.com",
#         "sender": "Ujjwal Sharma <Ujjwal.Sharma@ltimindtree.com>",
#         "subject": "Non matching cheques",
#         "body": "The cheques in this email do not match.\n\nThanks & Regards,\nUjjwal Sharma",
#         "attachments_zip_b64": "UEsFBgAAAAAAAAAAAAAAAAAAAAAAAA=="
#     },
#     {
#         "email_id": "u351720@gmail.com",
#         "sender": "u351720@gmail.com",
#         "subject": "Test",
#         "body": "Please update the documents and resubmit.",
#         "attachments_zip_b64": "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"
#     }
# ]

# def add_email_db(api_response):
#     # Process each email
#     for email in api_response:
#         email_doc = {
#             "email_id": email["email_id"],
#             "sender": email["sender"],
#             "subject": email["subject"],
#             "body": email["body"],
#             "attachments": []
#         }

#         if email["attachments_zip_b64"]:
#             extracted_files = decode_and_extract_zip(email["attachments_zip_b64"])
#             file_paths = [os.path.join("extracted_attachments", f) for f in extracted_files]
#             uploaded = upload_files(file_paths)
#             email_doc["attachments"] = [f["id"] for f in uploaded]

#         # Insert into MongoDB
#         emails_collection.insert_one(email_doc)

#     print("✅ All emails processed and inserted into MongoDB.")

import os
import sys
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from fetch_email_client import add_email_db, upload_files


# sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
# sys.path.append(os.path.dirname(os.path.abspath(__file__)))



import json
import re

# Function to clean and sanitize JSON content
def clean_json_content(json_content):
    # Remove invalid control characters
    print(type(json_content))
    json_content = re.sub(r'[\x00-\x1F\x7F]', '', json_content)
    
    return json_content

# Read the content of the fetch_response_sample.json file
with open('fetch_response_sample.json', 'r') as file:
    json_content = file.read()

# Clean the JSON content
cleaned_json_content = clean_json_content(json_content)

# Parse the cleaned JSON content
data = json.loads(cleaned_json_content)

json_string = json.dumps(data)



# Call the add_email_db function with the parsed data
# add_email_db(str(data))
add_email_db(json_string)


# from fastapi import FastAPI, HTTPException
# from pymongo import MongoClient
# from pydantic import BaseModel

# app = FastAPI()

# # MongoDB connection
# client = MongoClient("mongodb://localhost:27017/")
# db = client["your_database_name"]
# collection = db["your_collection_name"]

# @app.delete("/clear-collection")
# def clear_collection():
#     try:
#         result = collection.delete_many({})
#         return {"message": f"Deleted {result.deleted_count} documents."}
#     except Exception as e:
#         raise HTTPException(status_code=500, detail=str(e))
