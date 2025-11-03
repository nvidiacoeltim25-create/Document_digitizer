import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import base64
import email
from email.header import decode_header
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import imaplib
import io
import json
import os
import smtplib
from typing import Dict, List
import zipfile
from PIL import Image

from bson import ObjectId
from fastapi import File, HTTPException, UploadFile
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import pymongo
import requests
import utils.exampleOutputs as exampleOutputs
from utils.constants import MONGO_URL, attachments_folder
from mcp.server.fastmcp import FastMCP
from deepface import DeepFace
# import exampleOutputs as examples
import time
from tensorflow.keras.applications.resnet50 import ResNet50, preprocess_input
from tensorflow.keras.preprocessing import image
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np
from utils.constants import  SENDER_PASSWORD
# import nest_asyncio
# nest_asyncio.apply()


# # Create a folder for attachments if it doesn't exist
os.makedirs(attachments_folder, exist_ok=True)

# Connect to MongoDB
client = pymongo.MongoClient(MONGO_URL)
db = client["email_database"]
attachments_collection = db["attachments"]
emails_collection = db["emails"]
users_collection = db["users_collection"]
reference_documents_collection = db["reference_documents"]

# Initialize MCP server
mcp = FastMCP("API Tools")


# Function to convert image to base64
def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

def decode_base64_image(base64_string: str, filename: str) -> None:
    if base64_string.startswith('data:image/jpeg;base64,'):
        base64_string = base64_string.split(',')
    image_data = base64.b64decode(base64_string)
    with open(filename, 'wb') as f:
        f.write(image_data)


class EmailCredentials(BaseModel):
    email_id: str
    password: str

class AttachmentIDs(BaseModel):
    attachment_ids: List[str]

def get_imap_server(username):
    imap_servers = {
        "gmail.com": "imap.gmail.com",
        "outlook.com": "outlook.office365.com",
        "hotmail.com": "outlook.office365.com",
        "yahoo.com": "imap.mail.yahoo.com",
        "icloud.com": "imap.mail.me.com",
        "aol.com": "imap.aol.com",
    }
    domain = username.split('@')[-1]
    return imap_servers.get(domain, "Unknown IMAP server")

def fetch_email_details(mail, email_id):
    status, msg_data = mail.fetch(email_id, "(RFC822)")
    for response_part in msg_data:
        if isinstance(response_part, tuple):
            msg = email.message_from_bytes(response_part[1])
            sender = msg["From"]
            subject = decode_header(msg["Subject"])[0][0]
            if isinstance(subject, bytes):
                subject = subject.decode()
            body = ""
            attachments = []
            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    content_disposition = str(part.get("Content-Disposition"))
                    if "attachment" in content_disposition:
                        filename = part.get_filename()
                        if filename:
                            filepath = os.path.join(attachments_folder, filename)
                            if not os.path.exists(filepath):
                                with open(filepath, "wb") as f:
                                    f.write(part.get_payload(decode=True))
                            attachments.append(filename)
                    elif content_type == "text/plain" and "attachment" not in content_disposition:
                        body = part.get_payload(decode=True).decode()
            else:
                body = msg.get_payload(decode=True).decode()
            return {"sender": sender, "subject": subject, "body": body, "attachments": attachments}

@mcp.tool()
async def fetch_emails(email_id: str, password: str):
    """Fetch email details for the provided email_id and password"""
    imap_server_name = get_imap_server(email_id)
    if imap_server_name == "Unknown IMAP server":
        raise HTTPException(status_code=400, detail="Unsupported email domain")

    try:
        mail = imaplib.IMAP4_SSL(imap_server_name)
        mail.login(email_id, password)
        mail.select("inbox")
        status, messages = mail.search(None, "ALL")
        email_ids = messages[0].split()

        emails_list = []

        emails = []
        for email_id in email_ids:
            email_details = fetch_email_details(mail, email_id)
            email_attachments = []
        #     emails_list.append(email_details)
        # return emails_list

            # Check if email already exists in the database
            existing_email = emails_collection.find_one({"email_id": email_id, "subject": email_details["subject"]})
            if not existing_email:
                email_doc = {
                    "email_id": email_id,
                    "sender": email_details["sender"],
                    "subject": email_details["subject"],
                    "body": email_details["body"],
                    "attachments": []
                }
                email_id = emails_collection.insert_one(email_doc).inserted_id
            else:
                email_id = existing_email["_id"]
                email_attachments = existing_email["attachments"]

            # Save attachments to the database
            for attachment in email_details["attachments"]:
                attachment_doc = attachments_collection.find_one({"email_id": email_id, "attachment_name": attachment})
                if not attachment_doc:
                    attachment_doc = {
                        "email_id": email_id,
                        "attachment_name": attachment
                    }
                    attachment_id = attachments_collection.insert_one(attachment_doc).inserted_id
                    attachment_doc["_id"] = str(attachment_id)
                else:
                    attachment_doc["_id"] = str(attachment_doc["_id"])
                if attachment_doc["_id"] not in email_attachments:
                    email_attachments.append(attachment_doc["_id"])

            # Update the email document with the attachment ObjectIds
            emails_collection.update_one(
                {"_id": email_id},
                {"$set": {"attachments": email_attachments}}
            )

            email_details["attachments"] = email_attachments
            emails.append(email_details)

        mail.logout()
        return emails

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# class ObjectIDs(BaseModel):
#     object_ids: List[str]

def get_attachment_name(object_id):
    try:
        # Convert the string object_id to an ObjectId
        obj_id = ObjectId(object_id)
        
        # Find the document with the given object_id
        attachment = attachments_collection.find_one({"_id": obj_id})
        
        if attachment:
            return attachment.get("attachment_name", "Attachment name not found")
        else:
            return "Attachment not found"
    except Exception as e:
        return f"An error occurred: {e}"


@mcp.tool()
async def get_files():
    """Returns data related to all the files in database"""
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
                file_id_name[f"{file_name}"] = str(document["_id"])
            else:
                file_id_name[f"{file_name}"] = "File not found"

    print(file_id_name)
    
    response = file_id_name
    return response

@mcp.tool()
async def extract_data(object_id: str):
    """Extract data for given object_id"""
    # Get the attachment name using the object ID
    attachment_name = get_attachment_name(object_id)

    invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
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
        # elif file_path.lower().endswith('.pdf'):
        #     images = convert_from_path(file)
        #     encoded_image = image_to_base64(images[0])
        else:
            return {"error": "Unsupported file type"}

    

    payload = {
        'model': 'meta/llama-3.2-90b-vision-instruct',
        'messages': [
            {
                'role': 'user',
                'content': f'''
                You are a document verification system having the permission to extract data from all kinds of documents
                Extract data from <img src="data:image/png;base64,{encoded_image}" /> and provide it in a JSON format.
                Don't provide anything else in the output except the JSON.
                Here are example outputs {json.dumps(exampleOutputs.output_example1)} {json.dumps(exampleOutputs.output_example2)} {json.dumps(exampleOutputs.output_example3)} {json.dumps(exampleOutputs.output_example4)} {json.dumps(exampleOutputs.output_example5)} {json.dumps(exampleOutputs.output_example6)}
                '''
            }
        ],
        'max_tokens': 512,
        'temperature': 1.00,
        'top_p': 1.00,
    }
    
    response = requests.post(invoke_url, headers=headers, json=payload)
    # print(content['choices'][0]['message']['content'])

    
    if response.status_code == 200:
        try:
            content = response.json()
            if 'choices' in content and len(content['choices']) > 0:
                # print(content)
                # return json.loads(content['choices'][0]['message']['content'])
                extracted_data = json.loads(content['choices'][0]['message']['content'])
                
                # Update the attachments collection with the extracted data
                attachments_collection.update_one(
                    {"_id": ObjectId(object_id)},
                    {"$set": {"extraction": extracted_data}}
                )
                
                return extracted_data
            else:
                return {}
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return {}
    else:
        print(f"Request failed with status code {response.status_code}")
        return {}

@mcp.tool()
async def extract_json(object_id: str):

    """Extract data from file using mistral-small-latest"""
    document_id = ObjectId(object_id)
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
                    "text": 
                        f"""
                        Extract data from the given image and provide it in a JSON format.
                        Don't provide anything else in the output except the JSON.
                        Here are example outputs {json.dumps(exampleOutputs.output_example1)} {json.dumps(exampleOutputs.output_example2)} {json.dumps(exampleOutputs.output_example3)} {json.dumps(exampleOutputs.output_example4)} {json.dumps(exampleOutputs.output_example5)} {json.dumps(exampleOutputs.output_example6)}
                        """
                },
                {
                    "type": "document_url",
                    "document_url": signed_url.url,
                }
            ]
        }
    ]

    model = "mistral-small-latest"
    chat_response = client.chat.complete(
        model=model,
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

@mcp.tool()
async def delete_attachments(attachments: AttachmentIDs):
    """delete the attachments for given attachment_ids"""
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

@mcp.tool()
async def ask_question(json_data: str, question: str):
    """Answer the question according to given json_data"""
    invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json"
    }

    payload = {
        'model': 'meta/llama-3.2-90b-vision-instruct',
        'messages': [
            {
                'role': 'user',
                'content': f'''
                Here is the data: {json_data}
                Question: {question}
                Please provide a straightforward answer. If the information is not available in the data, respond with "This information is not available."
                Do not provide explaination on how you got the answer
                '''
            }
        ],
        'max_tokens': 512,
        'temperature': 0.1,
        'top_p': 1.00,
    }

    response = requests.post(invoke_url, headers=headers, json=payload)

    if response.status_code == 200:
        try:
            content = response.json()
            if 'choices' in content and len(content['choices']) > 0:
                answer = content['choices'][0]['message']['content'].strip()
                return {"answer": answer}
            else:
                return {"answer": "This information is not available."}
        except json.JSONDecodeError:
            raise HTTPException(status_code=500, detail="Error decoding JSON response")
    else:
        raise HTTPException(status_code=response.status_code, detail="Request failed")

@mcp.tool()
async def get_document_type(object_id: str):
    # Get the attachment name using the object ID
    attachment_name = get_attachment_name(object_id)

    invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
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
            encoded_image = image_to_base64(images)
        else:
            return {"error": "Unsupported file type"}

    payload = {
        'model': 'meta/llama-3.2-90b-vision-instruct',
        'messages': [
            {
                'role': 'user',
                'content': f'''
                You are a document verification system. Identify the type of document from the provided image.
                Respond in one word
                Choose word from ["passport", "driver's license", "cheque", "corporate resolution", "PAN card", "adhaar card", "shareholder's certificate", "affidavit"]
                Do not add any extra characters like "." in the output
                <img src="data:image/png;base64,{encoded_image}" />
                '''
            }
        ],
        'max_tokens': 512,
        'temperature': 1.00,
        'top_p': 1.00,
    }
    
    response = requests.post(invoke_url, headers=headers, json=payload)
    
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

class JsonList(BaseModel):
    data: List[Dict]

@mcp.tool()
async def generate_email(json_inputs: JsonList):
    """Generate required email from provided json data"""
    invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
    headers = {
        "Authorization": "Bearer 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",
        "Accept": "application/json"
    }
    
    prompt = f"""
    You are an AI document verifier. You will receive document information in JSON format. Your task is to verify the completeness and correctness of the information. If any information is missing or incorrect, generate an email requesting the person who submitted the documents to update and resubmit them with the necessary corrections.
    JSON Inputs:
    {generate_json_string(json_inputs)}
    
    Steps:
    Verify Each Field:
    Check if all required fields are present.
    Ensure the values in each field are correct and appropriately formatted.
    Identify Missing or Incorrect Information:
    List any fields that are missing.
    Note any fields with incorrect or improperly formatted information.
    Generate an Email:
    Use the provided email template to request updates.
    Include specific details about the missing or incorrect information.
    Required Fields:
    Board of Directors or Sole Director
    Laws of Country
    Held at
    On (Date)
    Holder Information (Name, Title, Signature)
    Dated
    Printed Name, Title
    CertificateNumber
    CompanyName
    ShareholderName
    CUSIP
    No of Shares
    PurchaseDate
    Class
    Signatory 1
    Signatory 2
    Medallion guarantee presence
    Account Name
    Account Number
    Name of Stock
    Social Security Number
    Undersigned
    Residing at
    Undersigned Role
    Died on
    Duration
    Undersigned signature present
    Sworn on
    Administer title
    Administer signature present
    Commission expires on
    License no
    Expires
    Name and address
    Sex
    Hair
    Ht
    Wt
    Eyes
    DOB
    Signature
    BorderSecurityFeature
    PayorName
    PayorAddress
    PayToName
    AmountNumber
    AmountString
    Date
    SerialNumber
    RoutingNumber
    BankName
    BankAddress
    Email Template:
    Subject: Request for Document Update and Resubmission
    Dear [Submitter's Name],
    We have reviewed the documents you submitted. Please find below the details of the missing or incorrect information:
    Board of Directors or Sole Director: [Missing/Incorrect Information]
    Laws of Country: [Missing/Incorrect Information]
    Held at: [Missing/Incorrect Information]
    On (Date): [Missing/Incorrect Information]
    Holder Information:
    Holder 1 Name: [Missing/Incorrect Information]
    Holder 1 Title: [Missing/Incorrect Information]
    Holder 1 Signature: [Missing/Incorrect Information]
    Holder 2 Name: [Missing/Incorrect Information]
    Holder 2 Title: [Missing/Incorrect Information]
    Holder 2 Signature: [Missing/Incorrect Information]
    Dated: [Missing/Incorrect Information]
    Printed Name, Title: [Missing/Incorrect Information]
    CertificateNumber: [Missing/Incorrect Information]
    CompanyName: [Missing/Incorrect Information]
    ShareholderName: [Missing/Incorrect Information]
    CUSIP: [Missing/Incorrect Information]
    No of Shares: [Missing/Incorrect Information]
    PurchaseDate: [Missing/Incorrect Information]
    Class: [Missing/Incorrect Information]
    Signatory 1: [Missing/Incorrect Information]
    Signatory 2: [Missing/Incorrect Information]
    Medallion guarantee presence: [Missing/Incorrect Information]
    Account Name: [Missing/Incorrect Information]
    Account Number: [Missing/Incorrect Information]
    Name of Stock: [Missing/Incorrect Information]
    Social Security Number: [Missing/Incorrect Information]
    Undersigned: [Missing/Incorrect Information]
    Residing at: [Missing/Incorrect Information]
    Undersigned Role: [Missing/Incorrect Information]
    Died on: [Missing/Incorrect Information]
    Duration: [Missing/Incorrect Information]
    Undersigned signature present: [Missing/Incorrect Information]
    Sworn on: [Missing/Incorrect Information]
    Administer title: [Missing/Incorrect Information]
    Administer signature present: [Missing/Incorrect Information]
    Commission expires on: [Missing/Incorrect Information]
    License no: [Missing/Incorrect Information]
    Expires: [Missing/Incorrect Information]
    Name and address: [Missing/Incorrect Information]
    Sex: [Missing/Incorrect Information]
    Hair: [Missing/Incorrect Information]
    Ht: [Missing/Incorrect Information]
    Wt: [Missing/Incorrect Information]
    Eyes: [Missing/Incorrect Information]
    DOB: [Missing/Incorrect Information]
    Signature: [Missing/Incorrect Information]
    BorderSecurityFeature: [Missing/Incorrect Information]
    PayorName: [Missing/Incorrect Information]
    PayorAddress: [Missing/Incorrect Information]
    PayToName: [Missing/Incorrect Information]
    AmountNumber: [Missing/Incorrect Information]
    AmountString: [Missing/Incorrect Information]
    Date: [Missing/Incorrect Information]
    SerialNumber: [Missing/Incorrect Information]
    RoutingNumber: [Missing/Incorrect Information]
    BankName: [Missing/Incorrect Information]
    BankAddress: [Missing/Incorrect Information]
    Kindly update the documents with the correct information and resubmit them at your earliest convenience.
    Thank you for your cooperation.
    Best regards,
    [Your Name]
    [Your Position]
    Directly generate the email and give only the email in response. Do not give any other thing.
    """
    
    payload = {
        "model": 'meta/llama-3.2-90b-vision-instruct',
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
    
    response = requests.post(invoke_url, headers=headers, json=payload)
    
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
                return {"subject": subject, "body": body}
            else:
                return {}
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return {}
    else:
        print(f"Request failed with status code {response.status_code}")
        return {}

@mcp.tool()
async def send_email(subject: str, body: str, receiver_email: str):
    """send email to receiver_email"""
    msg = MIMEMultipart()
    msg['To'] = receiver_email
    msg['Subject'] = subject
    sender_email = "u351720@gmail.com"
    sender_password = SENDER_PASSWORD
    
    msg.attach(MIMEText(body, 'plain'))
    
    try:
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        text = msg.as_string()
        server.sendmail(sender_email, receiver_email, text)
        server.quit()
        return {"message": "Email sent successfully!"}
    except Exception as e:
        return {"error": f"Failed to send email. Error: {e}"}

# ML FACE AND SIGNATURE COMPARISON

# Function to get image embedding
base_model = ResNet50(weights='imagenet', include_top=False, pooling='avg')
def get_image_embedding(img_path):
    img = image.load_img(img_path, target_size=(224, 224))
    img_data = image.img_to_array(img)
    img_data = np.expand_dims(img_data, axis=0)
    img_data = preprocess_input(img_data)
    embedding = base_model.predict(img_data)
    return embedding.flatten()

# Function to compare face images
def face_similarity_matching(img_path_1: str, img_path_2: str) -> Dict[str, str]:
    start_time = time.time()
    result = DeepFace.verify(img_path_1, img_path_2)
    similarity_score = round((1 - result['distance']), 4)
    end_time = time.time()
    time_taken = str(round((end_time - start_time), 4)) + " seconds"
    return {
        "similarity_score": str(similarity_score),
        "time_taken": time_taken
    }

# Function to compare signature images
def similarity_matching(img_path_1: str, img_path_2: str) -> float:
    embedding1 = get_image_embedding(img_path_1)
    embedding2 = get_image_embedding(img_path_2)
    similarity = cosine_similarity([embedding1], [embedding2])
    return float(similarity)  # Convert numpy.float64 to float before returning

# Endpoint to compare face images
@mcp.tool()
def compare_face_images(object_id_1: str, object_id_2: str) -> Dict[str, str]:
    """Compares faces in two files"""
    try:
        attachment_name_1 = get_attachment_name(object_id_1)
        attachment_name_2 = get_attachment_name(object_id_2)
        
        if "An error occurred" in attachment_name_1 or "Attachment not found" in attachment_name_1:
            raise HTTPException(status_code=404, detail=attachment_name_1)
        
        if "An error occurred" in attachment_name_2 or "Attachment not found" in attachment_name_2:
            raise HTTPException(status_code=404, detail=attachment_name_2)
        
        file_path_1 = os.path.join(attachments_folder, attachment_name_1)
        file_path_2 = os.path.join(attachments_folder, attachment_name_2)
        
        if not os.path.exists(file_path_1):
            raise HTTPException(status_code=404, detail="File 1 not found")
        
        if not os.path.exists(file_path_2):
            raise HTTPException(status_code=404, detail="File 2 not found")
        
        result = face_similarity_matching(file_path_1, file_path_2)
        return result
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# Endpoint to compare signature images
@mcp.tool()
def compare_signature_images(object_id_1: str, object_id_2: str) -> Dict[str, str]:
    """Compares signatures in two files"""
    try:
        attachment_name_1 = get_attachment_name(object_id_1)
        attachment_name_2 = get_attachment_name(object_id_2)
        
        if "An error occurred" in attachment_name_1 or "Attachment not found" in attachment_name_1:
            raise HTTPException(status_code=404, detail=attachment_name_1)
        
        if "An error occurred" in attachment_name_2 or "Attachment not found" in attachment_name_2:
            raise HTTPException(status_code=404, detail=attachment_name_2)
        
        file_path_1 = os.path.join(attachments_folder, attachment_name_1)
        file_path_2 = os.path.join(attachments_folder, attachment_name_2)
        
        if not os.path.exists(file_path_1):
            raise HTTPException(status_code=404, detail="File 1 not found")
        
        if not os.path.exists(file_path_2):
            raise HTTPException(status_code=404, detail="File 2 not found")
        
        start_time = time.time()
        similarity_score = similarity_matching(file_path_1, file_path_2)
        similarity_score = round(float(similarity_score), 4)  # Convert numpy.float64 to float before rounding
        end_time = time.time()
        time_taken = str(round((end_time - start_time), 4)) + " seconds"
        return {
            "similarity_score": str(similarity_score),
            "time_taken": time_taken
        }
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))

# LLM Features
# Uses meta/llama-4-maverick-17b-128e-instruct
def extract_json_from_string(input_string):
    try:
        # Find the start and end indices of the JSON object
        start_index = input_string.find('{')
        end_index = input_string.rfind('}') + 1
        
        if start_index != -1 and end_index != -1:
            json_str = input_string[start_index:end_index]
            # Convert the JSON string to a Python dictionary
            json_data = json.loads(json_str)
            return json_data
        else:
            return "No JSON object found in the input string"
    except json.JSONDecodeError as e:
        return f"Error decoding JSON: {e}"

@mcp.tool()
def cheque_signature_compare_llama4(object_id_1: str, object_id_2: str):
    """Compare signatures in given two documents"""
    image1_path = attachments_folder + "/" + get_attachment_name(object_id_1)
    image2_path = attachments_folder + "/" + get_attachment_name(object_id_2)
    api_key = "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"
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    model='meta/llama-4-maverick-17b-128e-instruct'
    max_tokens=512
    temperature=1.00 
    top_p=1.00
    stream=False

    with open(image1_path, "rb") as f:
        image1_b64 = base64.b64encode(f.read()).decode()

    with open(image2_path, "rb") as f:
        image2_b64 = base64.b64encode(f.read()).decode()

    assert len(image1_b64) < 180_000, \
        "To upload larger images, use the assets API (see docs)"

    assert len(image2_b64) < 180_000, \
        "To upload larger images, use the assets API (see docs)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }


    # <img src="data:image/png;base64,{image1_b64}" />
    # <img src="data:image/png;base64,{image2_b64}" />

    result_format = {
                    "comparison": "If the signatures are strictly of the same person return Pass otherwise return Fail. Only respond in Pass or Fail",
                    "explanation": "explanation for the given signature comparison result"
                    }
    result_example = {
                    "comparison": "",
                    "explanation": ""
                    }

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": f"""
                    Provided two bank check images
                    <img src="data:image/png;base64,{image1_b64}" />
                    <img src="data:image/png;base64,{image2_b64}" />
                    Compare the signature between both checks and provide comparison result
                    Use the below explanations
                    {json.dumps(result_format)}
                    Ensure that your responses are formatted correctly as JSON and contain only the necessary information requested.
                    Do not include any additional text or explanations or anything else outside of the JSON format.
                    example response format:
                    Do not add anything other than the response format given below.
                    {json.dumps(result_example)}
                    Do not provide anything else other than the json
                """
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": stream
    }

    start_time = time.time()
    response = requests.post(invoke_url, headers=headers, json=payload)
    end_time = time.time()

    if stream:
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        content = response.json()
        jsonString = content['choices'][0]['message']['content']

        # jsonObject = json.loads(jsonString)
        # execution_time = end_time - start_time
        return extract_json_from_string(jsonString)

@mcp.tool()
def verify_sharecert_seal_llama4(object_id_1: str):
    """Verify the seal present in provided shareholder certificate"""
    image1_path = attachments_folder + "/" + get_attachment_name(object_id_1)
    api_key = "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"
    invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
    model='meta/llama-4-maverick-17b-128e-instruct'
    max_tokens=512
    temperature=1.00 
    top_p=1.00
    stream=False

    with open(image1_path, "rb") as f:
        image1_b64 = base64.b64encode(f.read()).decode()

    assert len(image1_b64) < 180_000, \
        "To upload larger images, use the assets API (see docs)"

    headers = {
        "Authorization": f"Bearer {api_key}",
        "Accept": "text/event-stream" if stream else "application/json"
    }


    # <img src="data:image/png;base64,{image1_b64}" />

    payload = {
        "model": model,
        "messages": [
            {
                "role": "user",
                "content": f"""
                    Provided an image <img src="data:image/png;base64,{image1_b64}" />
                    Identify if it contains medallion signature or not
                    Respond yes medallion signature is present otherwise no 
                    Don't provide anything else in the output
                """
            }
        ],
        "max_tokens": max_tokens,
        "temperature": temperature,
        "top_p": top_p,
        "stream": stream
    }

    start_time = time.time()
    response = requests.post(invoke_url, headers=headers, json=payload)
    end_time = time.time()

    if stream:
        for line in response.iter_lines():
            if line:
                print(line.decode("utf-8"))
    else:
        
        content = response.json()
        print(f"CONTENT: {content}")
        jsonString = content['choices'][0]['message']['content']
        print(f"JSON STRING: {jsonString}")

        # jsonObject = json.loads(jsonString)
        # execution_time = end_time - start_time
        # return extract_json_from_string(jsonString)
        return jsonString


if __name__ == "__main__":
    print("Strating dd mcp server")
    mcp.run(transport="stdio")
