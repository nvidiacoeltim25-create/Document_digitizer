import json
import os
from bson import ObjectId
from fastapi import HTTPException
import pymongo
from mistralai import Mistral
import utils.exampleOutputs as examples

from models.models import ExtractModel
from utils.constants import MISTRAL_API_KEY, MISTRAL_MODEL, attachments_folder


client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["email_database"]
attachments_collection = db["attachments"]

client = Mistral(api_key=MISTRAL_API_KEY)

def mistral_infer_1(extract_model: ExtractModel, prompt: str):
    from utils.utils import convert_image_to_pdf, extract_json_from_string

    # attachment_name = get_attachment_name(extract_model.object_id)
    document_id = ObjectId(extract_model.object_id)
    attachment_doc = attachments_collection.find_one({"_id": document_id})
    if not attachment_doc:
        raise HTTPException(status_code=404, detail="Document not found")

    file_path = os.path.join(attachments_folder, attachment_doc["attachment_name"])
    extension = file_path[-4:]

    if extension != ".pdf":
        file_path = convert_image_to_pdf(file_path)

    uploaded_pdf = client.files.upload(
        file={
            "file_name": "uploaded_file1.pdf",
            "content": open(file_path, "rb"),
        },
        purpose="ocr"
    )

    signed_url = client.files.get_signed_url(file_id=uploaded_pdf.id)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "document_url",
                    "document_url": signed_url.url,
                }
            ]
        }
    ]

    chat_response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=messages,
    #     response_format = {
    #       "type": "json_object",
    #   }
    )
    # Debugging: Print the response content
    response_content = chat_response.choices[0].message.content
    response_content = extract_json_from_string(response_content)
    print("Response Content:", response_content)

    if not response_content:
        raise HTTPException(status_code=500, detail="Empty response from Mistral API")
    attachments_collection.update_one(
                    {"_id": ObjectId(extract_model.object_id)},
                    {"$set": {"extraction": response_content}}
                )

    # return json.loads(response_content)
    return response_content


def mistral_infer_2(file_path_1: str, file_path_2: str, prompt: str):
    # attachment_name = get_attachment_name(extract_model.object_id)
    # document_id = ObjectId(extract_model.object_id)
    # attachment_doc = attachments_collection.find_one({"_id": document_id})
    # if not attachment_doc:
    #     raise HTTPException(status_code=404, detail="Document not found")

    # file_path = os.path.join(attachments_folder, attachment_doc["attachment_name"])
    extension1 = file_path_1[-4:]
    extension2 = file_path_2[-4:]

    if extension1 != ".pdf":
        file_path_1 = convert_image_to_pdf(file_path_1)
    if extension2 != ".pdf":
        file_path_2 = convert_image_to_pdf(file_path_2)

    uploaded_pdf_1 = client.files.upload(
        file={
            "file_name": "uploaded_file1.pdf",
            "content": open(file_path_1, "rb"),
        },
        purpose="ocr"
    )

    uploaded_pdf_2 = client.files.upload(
        file={
            "file_name": "uploaded_file1.pdf",
            "content": open(file_path_2, "rb"),
        },
        purpose="ocr"
    )

    signed_url_1 = client.files.get_signed_url(file_id=uploaded_pdf_1.id)
    signed_url_2 = client.files.get_signed_url(file_id=uploaded_pdf_2.id)
    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                },
                {
                    "type": "document_url",
                    "document_url": signed_url_1.url,
                },
                {
                    "type": "document_url",
                    "document_url": signed_url_2.url,
                }
            ]
        }
    ]

    chat_response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=messages,
    #     response_format = {
    #       "type": "json_object",
    #   }
    )
    # Debugging: Print the response content
    response_content = chat_response.choices[0].message.content
    response_content = extract_json_from_string(response_content)
    print("Response Content:", response_content)

    if not response_content:
        raise HTTPException(status_code=500, detail="Empty response from Mistral API")

    # return json.loads(response_content)
    return response_content

def mistral_infer(prompt: str):

    messages = [
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": prompt
                }
            ]
        }
    ]

    chat_response = client.chat.complete(
        model=MISTRAL_MODEL,
        messages=messages,
    #     response_format = {
    #       "type": "json_object",
    #   }
    )
    # Debugging: Print the response content
    response_content = chat_response.choices[0].message.content
    response_content = extract_json_from_string(response_content)
    print("Response Content:", response_content)

    if not response_content:
        raise HTTPException(status_code=500, detail="Empty response from Mistral API")

    # return json.loads(response_content)
    return response_content




