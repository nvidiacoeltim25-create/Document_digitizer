
from fastapi import HTTPException
from io import BytesIO
import json
import os
import re
from typing import List
import uuid
import zipfile

from email_client.email_client import send_email
from email_client.fetch_email_client import add_email_db
from email_client.gen_email_prompt import get_prompt
from fastapi.responses import JSONResponse, StreamingResponse
from fastapi import UploadFile, File
import pymongo
import requests
from huggingface_client.hfClient import huggingface_infer, huggingface_infer_1
from mistral_client.mistral_client import mistral_infer, mistral_infer_1
from models.models import AttachmentIDs, ChatRequest, Compare, CompareChequesRequest, CompareModel, Config, CustomExtractModel, EmailIDs, EmailRequest, ExtractModel, FetchEmailRequest, GeneralEmailInput, JsonList, ObjectIDs, Response, SaveDataModel
from openai_client.openai_client import infer_openai_1
from utils.constants import EMAIL_FETCH_BASEURL, FACE_SIGN_COMPARE_BASEURL, FILE_TYPES, INVOKE_URL_NVIDIA, MCP_PORT, MODELS, NVIDIA_KEY, NVIDIA_MODEL, OPENAI_MODEL, PLATFORM, PLATFORMS
from utils.utils import cheque_signature_compare_llama4, clean_custom_fields_text, clean_mongo_doc, compare_cheques, genCustomFieldsPrompt, get_attachment_name, image_to_base64, verify_sharecert_seal_llama4
from utils.constants import INVOKE_URL_NVIDIA as invoke_url
from PIL import Image

import utils.exampleOutputs as examples
from utils.constants import config_file_path
from utils.constants import attachments_folder
from utils.constants import INVOKE_URL_NVIDIA as invoke_url
from bson.objectid import ObjectId
from bson.errors import InvalidId
from utils.prompts import extract_data_prompt, extract_text_prompt, sharecert_seal_prompt, cheque_signature_compare_prompt
import httpx
# from RAG_.rag_pipeline_UPLOAD import ingest_uploaded_docs , retrieve
# from RAG_.rag_pipeline import retrieve
os.makedirs(attachments_folder, exist_ok=True)



#start 
from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory assumed to be the current working directory
BASE_DIR = Path.cwd()

config_file_path = BASE_DIR / "config.json"
with open(config_file_path, 'r') as file:
    config = json.load(file)
#end

# Connect to MongoDB
client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["email_database"]
attachments_collection = db["attachments"]
emails_collection = db["emails"]
extractions_collection = db["extractions_collection"]
reference_documents_collection = db["reference_documents"]
cheques_collection = db["cheques_collection"]
tabular_custom_fields_coll = db["tabular_custom_fields_coll"]
NVIDIA_API_KEY = NVIDIA_KEY


async def getFilesByIdUtil(object_ids: ObjectIDs):
    files = []
    for object_id in object_ids.object_ids:
        attachment_name = get_attachment_name(object_id)
        if "An error occurred" in attachment_name or "Attachment not found" in attachment_name:
            raise HTTPException(status_code=404, detail=attachment_name)
        file_path = os.path.join(attachments_folder, attachment_name)
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail=f"File not found for object ID: {object_id}")
        files.append(file_path)
    
    # Create a zip file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_path in files:
            zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    
    return StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=files.zip"})


async def getAllFilesZipUtil():
    files = []
    file_id_name = []

    # Get all files in the attachments folder and their corresponding object IDs from MongoDB
    for file_name in os.listdir(attachments_folder):
        file_path = os.path.join(attachments_folder, file_name)
        if os.path.isfile(file_path):
            files.append(file_path)
            document = attachments_collection.find_one({"attachment_name": file_name})
            if document:
                file_id_name.append([str(document["_id"]), str(file_name)])
            else:
                file_id_name.append("File data not found")

    if not files:
        raise HTTPException(status_code=404, detail="No files found in the attachments folder")

    print(file_id_name)
    # Create a zip file in memory
    zip_buffer = BytesIO()
    with zipfile.ZipFile(zip_buffer, "w") as zip_file:
        for file_path in files:
            zip_file.write(file_path, os.path.basename(file_path))
    zip_buffer.seek(0)
    

    response = StreamingResponse(zip_buffer, media_type="application/zip", headers={"Content-Disposition": "attachment; filename=files.zip"})
    return response


async def getAllFilesInfoUtil():
    file_id_name = {}

    # Get all files in the attachments folder and their corresponding object IDs from MongoDB
    if len(os.listdir(attachments_folder)) == 0:
        return "No files found"
    for file_name in os.listdir(attachments_folder):
        file_path = os.path.join(attachments_folder, file_name)
        if os.path.isfile(file_path):
            document = attachments_collection.find_one({"attachment_name": file_name})
            if document:
                # file_id_name.append([str(document["_id"]), str(file_name)])
                # file_id_name[str(document["_id"])] = {
                #     # "file_type": document["file_type"],
                #     "file_name": file_name
                #     }
                file_id_name[f"{file_name}"] = str(document["_id"])
                
            else:
                file_id_name[f"{file_name}"] = "File not found"

    print(file_id_name)
    
    response = file_id_name
    return response   


async def extractDataUtil(extract_model: ExtractModel):
    # Get the attachment name using the object ID
    attachment_name = get_attachment_name(extract_model.object_id)

    # invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-11b-vision-instruct/chat/completions"
    headers = {
        "Authorization": f"Bearer {NVIDIA_KEY}",
        "Accept": "application/json"
    }
    
    if "An error occurred" in attachment_name or "Attachment not found" in attachment_name:
        return {"error": attachment_name}
    
    # Construct the file path
    file_path = os.path.join(attachments_folder, attachment_name)
    
    # Check if the file exists
    if not os.path.exists(file_path):
        return {"error": "File not found"}
    
    # Open the file and process it
    with open(file_path, "rb") as file:
        if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
            image = Image.open(file)
            encoded_image = image_to_base64(image)
        elif file_path.lower().endswith('.pdf'):
            images = convert_from_path(file)
            encoded_image = image_to_base64(images[0])
        else:
            return {"error": "Unsupported file type"}

    payload = {
        'model': NVIDIA_MODEL,
        'messages': [
            {
                'role': 'user',
                'content': f'''
                You are a document verification system having the permission to extract data from all kinds of documents
                Extract data from <img src="data:image/png;base64,{encoded_image}" /> and provide it in a JSON format.
                Don't provide anything else in the output except the JSON.
                Here are example outputs {json.dumps(examples.output_example1)} {json.dumps(examples.output_example2)} {json.dumps(examples.output_example3)} {json.dumps(examples.output_example4)} {json.dumps(examples.output_example5)} {json.dumps(examples.output_example6)}
                '''
            }
        ],
        'max_tokens': 512,
        'temperature': 1.00,
        'top_p': 1.00,
    }
    # extract_model.platform = "mistral"
    if PLATFORM == "nvidia":
        response = requests.post(invoke_url, headers=headers, json=payload)
        # print(content['choices'][0]['message']['content'])

        
        if response.status_code == 200:
            try:
                content = response.json()
                if 'choices' in content and len(content['choices']) > 0:
                    #print(content)
                    #return json.loads(content['choices'][0]['message']['content'])
                    extracted_data = json.loads(content['choices'][0]['message']['content'])
                
                    # Update the attachments collection with the extracted data
                    attachments_collection.update_one(
                        {"_id": ObjectId(extract_model.object_id)},
                        {"$set": {"extraction": extracted_data}}
                    )
                
                    return {"extracted_data": extracted_data}
                else:
                    return {}
            except json.JSONDecodeError:
                print("Error decoding JSON response")
                return {}
        else:
            print(f"Request failed with status code {response.status_code}")
            return {}
    elif PLATFORM == "huggingface":

        response = await huggingface_infer_1(filepath=file_path, prompt=extract_data_prompt)

        if response:
            attachments_collection.update_one(
                        {"_id": ObjectId(extract_model.object_id)},
                        {"$set": {"extraction": response}}
                    )
        return {"extracted_data": json.loads(response)}
    elif PLATFORM == "mistral":

        return mistral_infer_1(extract_model, extract_data_prompt)
    else:
        return "Incorrect platform\nUse: nvidia or huggingface or mistral"
    

async def extractCustomTabularDataUtil(custom_extract_model: CustomExtractModel):
    fields = custom_extract_model.customFields
    resp = []
    for object_id in custom_extract_model.ObjectIDs:
        attachment_name = get_attachment_name(object_id)
        file_path = os.path.join(attachments_folder, attachment_name)
        try:
            model_output = await huggingface_infer_1(file_path, genCustomFieldsPrompt(fields_list=fields))
            cleaned_json1 = clean_custom_fields_text(model_output)
    
            cleaned_string1 = cleaned_json1.replace('\\\"', '\"').replace('\\', '')

            confidence_prompt = f"""
            {str(cleaned_string1)}

            Add a confidence score from 0 to 100 depicting the correctness of data extracted by the LLM
            
            Give only the final json with the confidence score in the response
            Example outputs:
            
            {json.dumps(examples.out_ex_1)}
            
            {json.dumps(examples.out_ex_2)}

            Do not add any text in the response
            """

            # model_pass_2 = await huggingface_infer_1(file.filename, confidence_prompt)
            model_pass_2 = infer_openai_1(file_path, confidence_prompt)
            # print(model_pass_2)
            cleaned_json = clean_custom_fields_text(model_pass_2)
            # print(cleaned_json)
            cleaned_string = cleaned_json.replace('\\\"', '\"').replace('\\', '')
            # print(cleaned_string)
            fixed_str = re.sub(r'(\d+)"\s*\(([\d.]+)\)', r'\1\\" (\2)', cleaned_string)
            try:
                json_obj = json.loads(fixed_str)
                resp.append({object_id: json_obj})
            except json.JSONDecodeError as e:
                print("Failed to parse JSON:", e)
        # return {"response": resp}
        
        except Exception as e:
            return JSONResponse(content={"error": str(e)}, status_code=500)
    return {"response": resp}


async def generateEmailGeneralUtil(ge_input: GeneralEmailInput):

    prompt =  f"""
        Write an email report on the result of the action perfomed on the given list of images
        Image list : {ge_input.object_ids}
        Action: {ge_input.action}
        Result of the action: {ge_input.result}

        Output Format:
        Subject: <subject>
        Body: <body>
    """
    response = huggingface_infer(prompt=prompt)
    # message_content = content['choices'][0]['message']['content']
    subject_start = response.find("Subject:")
    subject_end = response.find("\n", subject_start)
    body_start = subject_end + 1
    subject = response[subject_start:subject_end].strip()
    body = response[body_start:].strip()
    # if PLATFORM == "huggingface":
    #     response = huggingface_infer(prompt=prompt)
    # elif PLATFORM == "mistral":
    #     response = mistral_infer(prompt=prompt)
    return {"subject": subject, "body": body}


async def generateEmailSchemaUtil(json_inputs: JsonList):
    prompt = get_prompt(json_inputs)
    if PLATFORM == "nvidia":
        # print("JSONINPUTS: ", json_inputs)
        # invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
        headers = {
            "Authorization": f"Bearer ${NVIDIA_KEY}",
            "Accept": "application/json"
        }
        
        payload = {
            "model": NVIDIA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 512,
            "temperature": 1.00,
            "top_p": 1.00,
        }
        
        response = await requests.post(invoke_url, headers=headers, json=payload)
        
        if response.status_code == 200:
            try:
                content = response.json()
                if 'choices' in content and len(content['choices']) > 0:
                    message_content = content['choices'][0]['message']['content']
                    subject_start = message_content.find("Subject:")
                    subject_end = message_content.find("\n", subject_start)
                    body_start = subject_end + 1
                    subject = message_content[subject_start:subject_end].strip()
                    body = message_content[body_start:].strip()
                    print("response: " , {"subject": subject, "body": body})
                    return {"subject": subject, "body": body}
                else:
                    return {}
            except json.JSONDecodeError:
                print("Error decoding JSON response")
                return {}
        else:
            print(f"Request failed with status code {response.status_code}")
            return {}
    elif PLATFORM == "mistral":
        message_content = mistral_infer(prompt=prompt)
        subject_start = message_content.find("Subject:")
        subject_end = message_content.find("\n", subject_start)
        body_start = subject_end + 1
        subject = message_content[subject_start:subject_end].strip()
        body = message_content[body_start:].strip()
        print("response: " , {"subject": subject, "body": body})
        return {"subject": subject, "body": body}
        # return mistral_infer(prompt=prompt)
    elif PLATFORM == "huggingface":
        message_content = huggingface_infer(prompt=prompt)
        subject_start = message_content.find("Subject:")
        subject_end = message_content.find("\n", subject_start)
        body_start = subject_end + 1
        subject = message_content[subject_start:subject_end].strip()
        body = message_content[body_start:].strip()
        print("response: " , {"subject": subject, "body": body})
        return {"subject": subject, "body": body}
        # return huggingface_infer(prompt=prompt)
    else:
        return {f"message": "ERROR use platforms: {PLATFROMS}"}


async def sendEmailUtil(emailRequst: EmailRequest):
    try:
        send_email(
            recipient_email=emailRequst.recipient_email,
            subject=emailRequst.subject,
            plain_text=emailRequst.html_content,
            html_content=emailRequst.html_content
        )
        return {"message": "Email sent successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def deleteAttachmentsUtil(attachments: AttachmentIDs):
    try:
        for attachment_id_str in attachments.attachment_ids:
            attachment_id = ObjectId(attachment_id_str)
            attachment_doc = attachments_collection.find_one({"_id": attachment_id})
            if not attachment_doc:
                raise HTTPException(status_code=404, detail=f"Attachment with ID {attachment_id_str} not found")

            # Delete the attachment file from the filesystem
            attachment_path = os.path.join(attachments_folder, attachment_doc["attachment_name"])
            if os.path.exists(attachment_path):
                os.remove(attachment_path)

            # Delete the attachment document from the database
            attachments_collection.delete_one({"_id": attachment_id})

        return {"detail": "Attachments deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def deleteEmailsUtil(email_ids: EmailIDs):
    try:
        for email_id_str in email_ids.email_ids:
            email_id = ObjectId(email_id_str)
            email_doc = emails_collection.find_one({"_id": email_id})
            if not email_doc:
                raise HTTPException(status_code=404, detail=f"Email with ID {email_id_str} not found")

            # Delete the email document from the database
            emails_collection.delete_one({"_id": email_id})

        return {"detail": "Emails deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def clearAllEmailsUtil():
    try:
        result = emails_collection.delete_many({})
        return {"message": f"Deleted {result.deleted_count} documents."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


async def compareChequesUtil(request: CompareChequesRequest):
    # Get the attachment names using the object IDs
    attachment_name_1 = get_attachment_name(request.object_id_1)
    attachment_name_2 = get_attachment_name(request.object_id_2)
    
    if "An error occurred" in attachment_name_1 or "Attachment not found" in attachment_name_1:
        raise HTTPException(status_code=404, detail=attachment_name_1)
    
    if "An error occurred" in attachment_name_2 or "Attachment not found" in attachment_name_2:
        raise HTTPException(status_code=404, detail=attachment_name_2)
    
    # Construct the file paths
    file_path_1 = os.path.join(attachments_folder, attachment_name_1)
    file_path_2 = os.path.join(attachments_folder, attachment_name_2)
    
    # Check if the files exist
    if not os.path.exists(file_path_1):
        raise HTTPException(status_code=404, detail="File 1 not found")
    
    if not os.path.exists(file_path_2):
        raise HTTPException(status_code=404, detail="File 2 not found")
    
    # Compare the cheques and get the result
    cheque1_data, cheque2_data, comparison_result = await compare_cheques(file_path_1, file_path_2, request.object_id_1, request.object_id_2)

    
# Overwrite results in MongoDB instead of inserting duplicates
    cheques_collection.update_one(
        {"object_id_1": request.object_id_1, "object_id_2": request.object_id_2},
        {
            "$set": {
                "cheque_data_1": cheque1_data,
                "cheque_data_2": cheque2_data,
                "extraction": comparison_result
            }
        },
        upsert=True
    )


    # cheques_collection.insert_one({
    #     "object_id_1": request.object_id_1,
    #     "object_id_2": request.object_id_2,
    #     "cheque_data_1": cheque1_data,
    #     "cheque_data_2": cheque2_data,
    #     "extraction": comparison_result,
    # })
    
    return {
        "cheque_1": cheque1_data,
        "cheque_2": cheque2_data,
        "comparison_result": comparison_result
    }


async def getDocumentTypeUtil(file_path: str):
    # attachment_name = get_attachment_name(object_id)
    # if "An error occurred" in attachment_name or "Attachment not found" in attachment_name:
    #     return {"error": attachment_name}

    # file_path = os.path.join(attachments_folder, attachment_name)

    if PLATFORM == "nvidia":
        headers = {
            "Authorization": f"Bearer {NVIDIA_KEY}",
            "Accept": "application/json"
        }

        if not os.path.exists(file_path):
            return {"error": "File not found"}

        with open(file_path, "rb") as file:
            if file_path.lower().endswith(('.png', '.jpg', '.jpeg')):
                image = Image.open(file)
                encoded_image = image_to_base64(image)
            elif file_path.lower().endswith('.pdf'):
                # images = convert_from_path(file)  # Uncomment if needed
                return {"error": "Unsupported file type .pdf"}
            else:
                return {"error": "Unsupported file type"}

        payload = {
            'model': NVIDIA_MODEL,
            'messages': [
                {
                    'role': 'user',
                    'content': f'''
                    You are a document verification system. Identify the type of document from the provided image.
                    Respond in one word
                    Choose word from {FILE_TYPES}
                    Do not add any extra characters like "." in the output
                    <img src="data:image/png;base64,{encoded_image}" />
                    '''
                }
            ],
            'max_tokens': 512,
            'temperature': 1.00,
            'top_p': 1.00,
        }

        response = requests.post(INVOKE_URL_NVIDIA, headers=headers, json=payload)

        if response.status_code == 200:
            try:
                content = response.json()
                if 'choices' in content and len(content['choices']) > 0:
                    return {"document_type": content['choices'][0]['message']['content']}
                else:
                    return {"error": "No document type identified"}
            except json.JSONDecodeError:
                return {"error": "Error decoding JSON response"}
        else:
            return {"error": f"Request failed with status code {response.status_code}"}

    elif PLATFORM == "huggingface":
        prompt = '''
        You are a document verification system. Identify the type of document from the provided image.
        Respond in one word
        Choose word from ["passport", "driver's license", "cheque", "corporate resolution", "PAN card", "adhaar card", "shareholder's certificate", "affidavit"]
        Do not add any extra characters like "." in the output'''
        response = await huggingface_infer_1(filepath=file_path, prompt=prompt)
        return response


async def verifyUtil(compare: Compare):
    new_image_name = get_attachment_name(compare.object_ids[0])
    if "An error occurred" in new_image_name or "Attachment not found" in new_image_name:
        raise HTTPException(status_code=404, detail=new_image_name)

    new_image_path = os.path.join(attachments_folder, new_image_name)
    if not os.path.exists(new_image_path):
        raise HTTPException(status_code=404, detail="New image file not found")

        
    # Validate function name and object IDs length based on function name
    if compare.function_name not in ["multimodal_verify", "verify_sharecert_sign", "verify_sharecert_seal", "cheque_signature_compare_llama4", "verify_sharecert_seal_llama4", "compare_cheques"]:
        raise HTTPException(status_code=400, detail="Invalid function name")

    if compare.function_name in ["multimodal_verify", "verify_sharecert_sign", "cheque_signature_compare_llama4", "compare_cheques"] and len(compare.object_ids) != 2:
        raise HTTPException(status_code=400, detail="Two object IDs are required for this function")

    if compare.function_name == "verify_sharecert_seal" and len(compare.object_ids) != 1:
        raise HTTPException(status_code=400, detail="One object ID is required for this function")
    
    if compare.function_name == "verify_sharecert_seal_llama4" and len(compare.object_ids) != 1:
        raise HTTPException(status_code=400, detail="One object ID is required for this function")

    
    new_image_name = get_attachment_name(compare.object_ids[0])
    if "An error occurred" in new_image_name or "Attachment not found" in new_image_name:
        raise HTTPException(status_code=404, detail=new_image_name)

    new_image_path = os.path.join(attachments_folder, new_image_name)
    if not os.path.exists(new_image_path):
        raise HTTPException(status_code=404, detail="New image file not found")

    if compare.function_name in ["multimodal_verify", "verify_sharecert_sign", "cheque_signature_compare_llama4"]:
        reference_image_name = get_attachment_name(compare.object_ids[1])
        if "An error occurred" in reference_image_name or "Attachment not found" in reference_image_name:
            raise HTTPException(status_code=404, detail=reference_image_name)

        reference_image_path = os.path.join(attachments_folder, reference_image_name)
        if not os.path.exists(reference_image_path):
            raise HTTPException(status_code=404, detail="Reference image file not found")

        if compare.function_name == "multimodal_verify":
            result = multimodal_verify(new_image_path, reference_image_path)
        elif compare.function_name == "cheque_signature_compare_llama4":
            result = cheque_signature_compare_llama4(new_image_path, reference_image_path, compare)
        else:
            result = verify_sharecert_sign(new_image_path, reference_image_path)


        
    else:
        result = await verify_sharecert_seal_llama4(new_image_path, compare.object_ids[0])
        return {"result": result}

    return result

async def fetchEmailUtil(fetch_email_model: FetchEmailRequest):
    # global EMAIL_FETCH_BASEURL
    config_file_path = BASE_DIR / "config.json"
    with open(config_file_path, 'r') as file:
        config = json.load(file)
    EMAIL_FETCH_BASEURL = config["fetch_email_link"]
    print("EMAIL_FETCH_BASEURL in fetchEmailUtil:", EMAIL_FETCH_BASEURL)

    #If no API URL, fetch from DB
    if EMAIL_FETCH_BASEURL == "":
        print("EMAIL_FETCH_BASEURL is empty, fetching emails from local DB")
        existing_email = emails_collection.find()
        email_list = [clean_mongo_doc(email) for email in existing_email]
        print("Number of emails fetched from DB:", len(email_list))

        newList = []
        for email in email_list:
            if '_id' in email:
                del email['_id']
            newList.append(email)

        return newList

    # fetching from external API
    try:
        print("Sending request to external API...")
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"{EMAIL_FETCH_BASEURL}/fetch_emails/", json=fetch_email_model.dict())
            print("Response status code:", response.status_code)
            print("Response text (truncated):", response.text[:500])

            if response.status_code != 200:
                print("API did not return success. Fetching from DB instead.")
                existing_email = emails_collection.find()
                email_list = [clean_mongo_doc(email) for email in existing_email]
                print("Number of emails fetched from DB:", len(email_list))

                newList = []
                for email in email_list:
                    if '_id' in email:
                        del email['_id']
                    newList.append(email)

                return newList

            print("API call successful. Proceeding to update DB...")

            # Clear DB only after successful API response
            deleted_result = emails_collection.delete_many({})
            print("Number of emails deleted:", deleted_result.deleted_count)

            print("Calling add_email_db to store emails in DB...")
            await add_email_db(response.text)

            print("Fetching emails from DB after storing...")
            existing_email = emails_collection.find()
            email_list = [clean_mongo_doc(email) for email in existing_email]
            print("Number of emails fetched from DB after API call:", len(email_list))

            newList = []
            for email in email_list:
                if '_id' in email:
                    del email['_id']
                newList.append(email)

            return newList

    except httpx.RequestError as e:
        print("RequestError occurred:", str(e))
        print("Falling back to existing DB records...")
        existing_email = emails_collection.find()
        email_list = [clean_mongo_doc(email) for email in existing_email]
        print("Number of emails fetched from DB:", len(email_list))

        newList = []
        for email in email_list:
            if '_id' in email:
                del email['_id']
            newList.append(email)

        return newList

    except httpx.HTTPStatusError as e:
        print("HTTPStatusError occurred:", str(e))
        print("Falling back to existing DB records...")
        existing_email = emails_collection.find()
        email_list = [clean_mongo_doc(email) for email in existing_email]
        print("Number of emails fetched from DB:", len(email_list))

        newList = []
        for email in email_list:
            if '_id' in email:
                del email['_id']
            newList.append(email)

        return newList



async def saveDataUtil(item: SaveDataModel):
    # Convert data string to JSON
    if isinstance(item.data, str):
        data_json = json.loads(item.data)
    else:
        data_json = item.data

    # Create a document to insert into MongoDB
    document = {
        "function": item.function,
        "object_ids": item.object_ids,
        "data": data_json
    }

    if item.function == "extract" and len(item.object_ids) == 1:
        result = extractions_collection.insert_one(document)
    elif item.function == "compare" and len(item.object_ids) == 2:
        result = extractions_collection.insert_one(document)
    else:
        return {"message": "ERROR: 1 id for extract and 2 id for compare"}

    # Add the inserted _id to the document and convert ObjectId to string
    document["_id"] = str(result.inserted_id)

    return {
        "message": "SUCCESS: Data saved successfully",
        "data": document
    }


async def mcpChatUtil(request: ChatRequest):
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            response = await client.post(f"http://127.0.0.1:{MCP_PORT}/chat", json=request.dict())
            response.raise_for_status()
            return Response(**response.json())
    except httpx.RequestError as e:
        raise HTTPException(status_code=502, detail=f"Request failed: {e}")
    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=e.response.status_code, detail=f"Upstream error: {e.response.text}")


async def compareFaceSignUtil(compare_model: CompareModel):
    if compare_model.function == "face":
        response = requests.post(f"{FACE_SIGN_COMPARE_BASEURL}/compare_face", json=compare_model.dict())
        withId = {
            "response": response.json(),
            "object_id_1": compare_model.object_id_1,
            "object_id_2": compare_model.object_id_2,
            "file_name_1": get_attachment_name(compare_model.object_id_1),
            "file_name_2": get_attachment_name(compare_model.object_id_2)
        }
        return withId
    elif compare_model.function == "sign":
        response = requests.post(f"{FACE_SIGN_COMPARE_BASEURL}/compare_signature", json=compare_model.dict())
        withId = {
            "response": response.json(),
            "object_id_1": compare_model.object_id_1,
            "object_id_2": compare_model.object_id_2,
            "file_name_1": get_attachment_name(compare_model.object_id_1),
            "file_name_2": get_attachment_name(compare_model.object_id_2)
        }
        
        return withId


async def getSavedDataUtil(data_id: str):
    try:
        object_id = ObjectId(data_id)
    except InvalidId:
        raise HTTPException(status_code=400, detail="Invalid ObjectId format")

    data = extractions_collection.find_one({"_id": object_id})
    if not data:
        raise HTTPException(status_code=404, detail="Data not found")

    # Convert ObjectId to string for JSON serialization
    data["_id"] = str(data["_id"])
    return {"message": "SUCCESS: Data retrieved successfully", "data": data}


async def getReferenceDocsUtil():
    documents = reference_documents_collection.find()
    result = []
    for document in documents:
        # result[document["file_name"]] = str(document["_id"])
        result.append([
            str(document["_id"]),
            document["file_name"]
        ])
    print(result)
    return result


async def uploadFilesUtil(files: List[UploadFile] = File(...)):
    # response = upload_files_function(files)
    # return response
    uploaded_files = []

    for file in files:
        # Generate a unique filename with the original extension
        file_extension = os.path.splitext(file.filename)[1]
        print(file_extension)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        attachment_path = os.path.join(attachments_folder, unique_filename)


        # Save the file
        with open(attachment_path, 'wb') as f:
            f.write(await file.read())
        
        # # Get file type
        # type_of_file = await get_document_type_function(attachment_path)
        # if type_of_file.lower() in FILE_TYPES:
        #     file_type = type_of_file
        # else:
        #     file_type = "undefined"

        # Store metadata in the database
        attachment_data = {
            "original_user_filename": file.filename,
            "attachment_name": unique_filename,
            # "file_type": file_type
        }
        result = attachments_collection.insert_one(attachment_data)

        uploaded_files.append({
            "original_name": file.filename,
            "stored_name": unique_filename,
            "id": str(result.inserted_id)
        })

    return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files}



# async def uploadFilesUtil_ingest(files: List[UploadFile] = File(...)):
#     # response = upload_files_function(files)
#     # return response
#     uploaded_files = []
#     attachment_paths_list = []

#     for file in files:
#         # Generate a unique filename with the original extension
#         file_extension = os.path.splitext(file.filename)[1]
#         print(file_extension)
#         unique_filename = f"{uuid.uuid4()}{file_extension}"
#         attachment_path = os.path.join(attachments_folder, unique_filename)
#         attachment_paths_list.append(attachment_path)

#         # Save the file
#         with open(attachment_path, 'wb') as f:
#             f.write(await file.read())
        
#         # # Get file type
#         # type_of_file = await get_document_type_function(attachment_path)
#         # if type_of_file.lower() in FILE_TYPES:
#         #     file_type = type_of_file
#         # else:
#         #     file_type = "undefined"

#         # Store metadata in the database
#         attachment_data = {
#             "original_user_filename": file.filename,
#             "attachment_name": unique_filename,
#             # "file_type": file_type
#         }
#         result = attachments_collection.insert_one(attachment_data)
        
#         uploaded_files.append({
#             "original_name": file.filename,
#             "stored_name": unique_filename,
#             "id": str(result.inserted_id)
#         })
#     ingest_uploaded_docs(attachment_paths_list)
#     return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files}


with open(config_file_path, 'r') as file:
    config = json.load(file)


async def getConfigUtil():
    try:
        with open(config_file_path, 'r') as file:
            config = json.load(file)
        return config
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Configuration file not found")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Error decoding JSON file")


async def updateConfigUtil(new_config: Config):
    try:
        if config["platform"] not in PLATFORMS:
            return {"message": f"ERROR use platform {PLATFORMS}"}
        # if config["model"] not in MODELS:
        #     return {"message": f"ERROR use platform {MODELS}"}
        with open(config_file_path, 'w') as file:
            json.dump(new_config.dict(), file, indent=4)
        return new_config
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error updating configuration file: {e}")


    # try:
    #     config_dict = new_config.dict()

    #     if config_dict["platform"] not in PLATFORMS:
    #         raise HTTPException(status_code=400, detail=f"ERROR: use platform from {PLATFORMS}")
    #     if config_dict["huggingface_model"].split("/")[-1] not in MODELS:
    #         raise HTTPException(status_code=400, detail=f"ERROR: use model from {MODELS}")

    #     with open(config_file_path, 'w') as file:
    #         json.dump(config_dict, file, indent=4)

    #     return new_config
    # except Exception as e:
    #     raise HTTPException(status_code=500, detail=f"Error updating configuration file: {e}")

async def rag_chatbot(query: str) -> str:
    print(f"Processing query: {query}")
    # ctx = retrieve(query)
    # if not ctx:
    #     print("No relevant context found.")
    #     return "No relevant info."

    # prompt = f"Context:\n{' '.join(ctx)}\n\nQuestion: {query}\nAnswer:"
    response = requests.post('http://localhost:8006/rag-chatbot',
            headers={
                'accept': 'application/json',
                'Content-Type': 'application/json'
            },
            json={
                "query": "When was the settlement agreement made?"
            }
        )

    # Get the response
    if response.status_code == 200:
        print(" *****LLM response received successfully")
        result = response.json()
        print(result)
        return result
    else:
        print(f"LLM request failed: {e}")
        return(f"Error: {response.status_code} - {response.text}")

    