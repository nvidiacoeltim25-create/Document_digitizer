import json
import sys
import pymongo
import base64
import io
import zipfile
import os
import requests
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from utils.utils import clean_json_content, upload_files_function

# MongoDB connection
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["email_database"]
emails_collection = db["emails"]

# Function to decode and extract ZIP
def decode_and_extract_zip(base64_string, output_folder="extracted_attachments"):
    zip_data = base64.b64decode(base64_string)
    zip_buffer = io.BytesIO(zip_data)
    with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
        os.makedirs(output_folder, exist_ok=True)
        zip_ref.extractall(output_folder)
        return zip_ref.namelist()

# # Function to upload files
# def upload_files(file_paths):
#     files = [('files', (os.path.basename(path), open(path, 'rb'))) for path in file_paths]
#     response = requests.post("http://localhost:8003/upload/", files=files)
#     if response.status_code == 200:
#         return response.json().get("uploaded_files", [])
#     else:
#         print("Upload failed:", response.text)
#         return []


# def upload_files(file_paths):
    # files = []
    # for path in file_paths:
    #     with open(path, 'rb') as f:
    #         files.append(('files', (os.path.basename(path), f.read())))
    # response = requests.post("http://localhost:8003/upload/", files=files)
    # if response.status_code == 200:
    #     return response.json().get("uploaded_files", [])
    # else:
    #     print("Upload failed:", response.text)
    #     return []

# upload_files(['/home/ujjwal-ltim/ujjwal/testDD/Document_Digitizer/reference_db/affidavit.jpg'])

async def add_email_db(api_response):
    try:
        emails = json.loads(api_response)  # Convert JSON string to list of dicts
        print("\n\n Keys in retrieved email response : ",emails['emails'][0].keys())
    except json.JSONDecodeError as e:
        print("❌ Failed to parse JSON:", e)
        return
    
    for email in emails['emails']:
        print("\n\nEmail in loop : ",email["subject"])
        
        email_doc = {
            "sender": email["email"],
            "subject": email["subject"],
            "body": email["body"],
            "attachments": []
        }
        # print(1)
        if email.get("attachments_zip_b64"):
            # print(" Attachment found. Decoding and extracting ZIP...")

            extracted_files = decode_and_extract_zip(email["attachments_zip_b64"])
            # print("Extracted files:", extracted_files)

            file_paths = [os.path.join("extracted_attachments", f) for f in extracted_files]
            # print(" File paths for upload:", file_paths)
            
            uploaded = await upload_files_function(file_paths)
            # print(" Uploaded file info:", uploaded)

            email_doc["attachments"] = [f["id"] for f in uploaded["uploaded_files"]]
            # print(6)
       
        email_db_result = emails_collection.insert_one(email_doc)
        print("\n\n Email inserted into MongoDB : ", email_db_result)
    print("Number of records inserted to emails db : ",len(emails['emails']))

    print("✅ All emails processed and inserted into MongoDB.")


