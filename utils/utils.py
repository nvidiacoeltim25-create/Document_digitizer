# Function to convert image to base64
import base64
from datetime import datetime
import io
import json
import os
import re
import time
from typing import List
import uuid
from PIL import Image
from bson.objectid import ObjectId
from fastapi import File, UploadFile, HTTPException, FastAPI, Query
from mistral_client.mistral_client import mistral_infer_1, mistral_infer_2
from models.models import Compare, ExtractModel
import pymongo
import shutil
import httpx

import requests

from huggingface_client.hfClient import huggingface_infer_1, huggingface_infer_2
from utils.constants import FILE_TYPES, HUGGINGFACE_KEY, INVOKE_URL_NVIDIA, NVIDIA_KEY, NVIDIA_MODEL, NVIDIA_MODEL_LLAMA4, PLATFORM, attachments_folder
from utils.constants import INVOKE_URL_NVIDIA as invoke_url
import utils.exampleOutputs as examples
from utils.prompts import cheque_signature_compare_prompt, extract_text_prompt, sharecert_seal_prompt
from langchain_nvidia_ai_endpoints import ChatNVIDIA
from huggingface_hub import InferenceClient

client = pymongo.MongoClient("mongodb://localhost:27017/")
db = client["email_database"]
attachments_collection = db["attachments"]

# Dummy function to get attachment name using object ID
def get_attachment_name(object_id: str) -> str:
    try:
        obj_id = ObjectId(object_id)
        attachment = attachments_collection.find_one({"_id": obj_id})
        if attachment:
            # return attachment.get("attachment_name", "Attachment name not found")
            return attachment["attachment_name"]
        else:
            return "Attachment not found"
    except Exception as e:
        return f"An error occurred: {e}"

def image_to_base64(image):
    buffered = io.BytesIO()
    image.save(buffered, format="PNG")
    img_str = base64.b64encode(buffered.getvalue()).decode()
    return img_str

# Function to decode base64 image
def decode_base64_image(base64_string: str, filename: str) -> None:
    if base64_string.startswith('data:image/jpeg;base64,'):
        base64_string = base64_string.split(',')
    image_data = base64.b64decode(base64_string)
    with open(filename, 'wb') as f:
        f.write(image_data)

def convert_image_to_pdf(image_path):
    image = Image.open(image_path)
    pdf_path = "output.pdf"
    image.save(pdf_path, "PDF", resolution=100.0)
    return pdf_path

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


def clean_text_email(text):
    # This regex keeps letters, digits, whitespace, and selected punctuation.
    cleaned = re.sub(r"[^\w\s.,:!=/-]", "", text)
    return cleaned


def convert_to_json(dirtyJson):
    return json.dumps(dirtyJson, indent=4)

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
    
def read_string_from_file(file_path):
    with open(file_path, 'r') as file:
        content = file.read()
    return content

# Function to clean and sanitize JSON content
def clean_json_content(json_content):
    # Remove invalid control characters
    json_content = re.sub(r'[\x00-\x1F\x7F]', '', json_content)
    return json_content

async def upload_files_function(files):
    uploaded_files = []

    for file_path in files:
        # # Generate a unique filename with the original extension
        file_extension = os.path.splitext(file_path)[1]
        # print(file_extension)
        unique_filename = f"{uuid.uuid4()}{file_extension}"
        attachment_path =  os.path.join(attachments_folder, unique_filename)
        
        shutil.copyfile(file_path, attachment_path)

        # Save the file
        # with open(attachment_path, 'wb') as f:
        #     f.write(await file_path.read())
        
        # with open(file_path, 'r') as f:
        #     f.read(await file_path.read())

        # Store metadata in the database
        attachment_data = {
            "original_user_filename": file_path.split("/")[-1],
            "attachment_name": unique_filename
        }
        result = attachments_collection.insert_one(attachment_data)
        print("\n\n Response while inserting record in attachments_collection : ",result)

        uploaded_files.append({
            "original_name": file_path.split("/")[-1],
            "stored_name": attachment_path,
            "id": str(result.inserted_id)
        })

    return {"message": "Files uploaded successfully", "uploaded_files": uploaded_files}




import json
import csv

def json_to_csv(json_string: str, output_file: str):
    """
    Converts a JSON string with individual keys for each field into a CSV file.

    Parameters:
    - json_string (str): The JSON string to convert.
    - output_file (str): Path to the output CSV file.
    """
    try:
        # Clean up the JSON string by removing escaped backslashes
        cleaned_string = json_string.replace('\\\"', '\"').replace('\\', '')
        
        # Parse the cleaned JSON string
        data = json.loads(cleaned_string)
        if not data or not isinstance(data, list):
            raise ValueError("Empty or invalid JSON data.")

        # Extract headers from the first dictionary
        headers = list(data[0].keys())

        # Write to CSV
        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=headers)
            writer.writeheader()
            for item in data:
                writer.writerow(item)

        print(f"CSV file created successfully at: {output_file}")
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")


def genCustomFieldsPrompt(fields_list):
    # Build the field list for the prompt
    field_lines = "\n".join([f"- {field}" for field in fields_list])

    # Create the JSON structure with each field as a key and empty string as value
    json_fields = ",\n        ".join([f'"{field}": ""' for field in fields_list])
    json_structure = "[\n    {\n        " + json_fields + "\n    }\n]"

    # Final prompt
    extract_data_prompt = f"""
You are a document data extraction system. From the given document, extract only the relevant fields based on its format.

If the document contains:
{field_lines}

Then extract those fields in the following JSON format:
{json_structure}

Do not include any explanation or extra text—only the JSON content.
"""

    return extract_data_prompt


def genCustomFieldsPromptWithScore(fields_list):
    # Build the field list for the prompt
    field_lines = "\n".join([f"- {field}" for field in fields_list])

    # Create the JSON structure with each field as a key and empty string as value
    json_fields = ",\n        ".join([f'"{field}": ""' for field in fields_list])
    json_fields += ',\n        "confidence score": 0'  # Add confidence score key
    json_structure = "[\n    {\n        " + json_fields + "\n    }\n]"

    # Final prompt
    extract_data_prompt = f"""
You are a document data extraction system. From the given document, extract only the relevant fields based on its format.

If the document contains:
{field_lines}

Then extract those fields in the following JSON format:
{json_structure}

The key "confidence score" will be a number between 0 and 100 depicting how confident the llm is in detecting the data for that row accurately

Each field should be a separate key in the JSON object. Do not combine multiple fields into a single key.

Do not include any explanation or extra text—only the JSON content.
"""

    return extract_data_prompt


def clean_custom_fields_text(input_text: str) -> str:
    input_text = re.sub(r'(\d+)""', r'\1\\"', input_text)
    input_text = re.sub(r'(\d+)"', r'\1\\"', input_text)
    json_match = re.search(r'\[\s*{.*?}\s*\]', input_text, re.DOTALL)
    return json_match.group(0) if json_match else None



# CHEQUE COMPARISION HUGGINGFACE llama-3.2-90b-vision-instruct
async def extract_text_from_image(image_path, invoke_url, headers, object_id):
    with open(image_path, "rb") as f:
        encoded_image = base64.b64encode(f.read()).decode()
    

    if PLATFORM == "nvidia":
        payload = {
            "model": NVIDIA_MODEL,
            "messages": [
                {
                    "role": "user",
                    "content": f'''
                    Extract the text from <img src="data:image/png;base64,{encoded_image}" /> according to this JSON format: {json.dumps(examples.json_schema7)}
                    Don't provide anything else in the output except the JSON
                    Format of date should be: "YYYY-MM-DD"
                    amountNumber should contain the amount written after dollar symbol
                
                    {json.dumps(examples.output_example7)}
                    '''
                }
            ],
            "max_tokens": 512,
            "temperature": 0.1,
            "top_p": 1.00,
        }
        response = requests.post(invoke_url, headers=headers, json=payload)
        if response.status_code == 200:
            try:
                return response.json()
                # print(response.json())
            except json.JSONDecodeError:
                print("Error decoding JSON response")
                return None
    elif PLATFORM == "huggingface":
 
        response = await huggingface_infer_1(image_path, extract_text_prompt)
        try:
            return response
            # print(response.json())
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return None
    elif PLATFORM == "mistral":
        extract_data_model = ExtractModel(object_id=object_id, platform=PLATFORM)
       
        response = mistral_infer_1(extract_data_model, extract_text_prompt)

        try:
            return response
            # print(response.json())
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return None
    else:
        return {"message": "ERROR: Platform can be nvidia, huggingface, mistral"}
    # print(response, response.text)
    
    if response.status_code == 200:
        try:
            return response.json()
            # print(response.json())
        except json.JSONDecodeError:
            print("Error decoding JSON response")
            return None
    else:
        print(f"Request failed with status code {response.status_code}")
        return None

def calculate_age_of_cheque(cheque_date_str):
    cheque_date = datetime.strptime(cheque_date_str, "%Y-%m-%d")
    current_date = datetime.now()
    age_in_days = (current_date - cheque_date).days
    return age_in_days

def extract_content(response):
    if response and 'choices' in response and len(response['choices']) > 0:
        return response['choices'][0]['message']['content']
    else:
        return ""

def clean_content(raw_content):
    start_index = raw_content.find("{")
    end_index = raw_content.rfind("}") + 1
    if start_index != -1 and end_index != -1:
        return raw_content[start_index:end_index]
    else:
        return ""

def clean_amount_field(json_content):
    try:
        data = json.loads(json_content.replace("'", "\""))
        if "amount" in data:
            data["amount"] = float(str(data["amount"]).replace(",", ""))
        return json.dumps(data)
    except json.JSONDecodeError:
        print("Error decoding JSON content amount field")
        return json_content

def add_age_in_days(json_content):
    try:
        data = json.loads(json_content.replace("'", "\""))
        data["age_in_days"] = calculate_age_of_cheque(data["date"])
        return json.dumps(data)
    except json.JSONDecodeError:
        print("Error decoding JSON content age")
        return json_content

def normalize_date(date_str):
    for fmt in ("%Y-%m-%d", "%d/%m/%y", "%b %d %Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str

def compare_amount(cheque_content):

    try:
        data = json.loads(cheque_content.replace("'", "\""))
        # data["age_in_days"] = calculate_age_of_cheque(data["date"])


        client = ChatNVIDIA(
        model="writer/palmyra-fin-70b-32k",
        # model="meta/llama-3.1-70b-instruct",
        api_key=NVIDIA_KEY, 
        temperature=0.1,
        top_p=1,
        max_tokens=32,
        )

        prompt=f'''convert the amount written in words ({data['amountString']}) to numbers. 
        Always provide the converted number in the output and nothing else
                            Example1:
                            input: seven hundred fifteen and 39/100
                            output: 715.39

                            Example2:
                            input: seventy four dollars and 69/100
                            output: 74.69

                            Example3:
                            input: five hundred dollars and 00/100
                            output: 500.00
                '''

        output=client.invoke(prompt)

  

        print(output.content)
        # data["amountSNComparison"] = f"{completion.choices[0].message.content}"
        if output.content==str(data['amountNumber']):
            data["amountSNComparison"] = "True"
        else:
            data["amountSNComparison"] = "False"

        return json.dumps(data)
    except json.JSONDecodeError:
        print("Error decoding JSON content compare amount nvidia")
        return cheque_content

def compare_amount_hf(cheque_content):

    try:
        data = json.loads(cheque_content.replace("'", "\""))
        # data["age_in_days"] = calculate_age_of_cheque(data["date"])

        client = InferenceClient(api_key=HUGGINGFACE_KEY)

        messages = [
            {
                "role": "user",
                "content": f'''convert the amount written in words ({data['amountString']}) to numbers. Only provide the converted number in the output and nothing else
                            Example1:
                            input: seven hundred fifteen and 39/100
                            output: 715.39

                            Example2:
                            input: seventy four dollars and 69/100
                            output: 74.69

                            Example3:
                            input: five hundred dollars and 00/100
                            output: 500.00
                '''
                # "content": f"compare the amount written in words ({data['amountString']}) with the amount written in numbers ({data['amountNumber']}). Check if they represent the same amount and return only True or False. Respond with true or false and nothing else."
                # "content": f"Compare the amount witten in words({data['amountString']}) and amount written in numbers({data['amountNumber']}) to check if it is the same amount, return only True or False. Do not provide explaination."
            }
        ]

        completion = client.chat.completions.create(
            # model="meta-llama/Llama-3.1-70B-Instruct", 
            model="meta-llama/Llama-3.2-3B-Instruct", 
            messages=messages, 
            max_tokens=100,
            # temperature= 0.1,
            # top_p= 1.00
        )

        print(completion.choices[0].message.content)
        # data["amountSNComparison"] = f"{completion.choices[0].message.content}"
        if completion.choices[0].message.content==str(data['amountNumber']):
            data["amountSNComparison"] = "True"
        else:
            data["amountSNComparison"] = "False"

        return json.dumps(data)
    except json.JSONDecodeError:
        print("Error decoding JSON content compare amount Huggingface")
        return cheque_content

# invoke_url = "https://integrate.api.nvidia.com/v1/chat/completions"
async def compare_cheques(new_image, reference_image, object_id_1, object_id_2):
    comparison_result = {}
    try:
        # invoke_url = "https://ai.api.nvidia.com/v1/gr/meta/llama-3.2-90b-vision-instruct/chat/completions"
        headers = {
            "Authorization": f"Bearer {NVIDIA_KEY}",
            "Accept": "application/json"
        }

        cheque1_response = await extract_text_from_image(new_image, invoke_url, headers, object_id_1)
        # print(f"CHEQUE1: {cheque1_response}")
        time.sleep(2)
        cheque2_response = await extract_text_from_image(reference_image, invoke_url, headers, object_id_2)
        # print(f"CHEQUE2: {cheque2_response}")

        cheque1_content = ""
        cheque2_content = ""
        PLATFORM = "huggingface"
        if PLATFORM == "nvidia":
            cheque1_content_raw = extract_content(cheque1_response)
            cheque2_content_raw = extract_content(cheque2_response)
            cheque1_content = clean_content(cheque1_content_raw)
            cheque2_content = clean_content(cheque2_content_raw)
          
        elif PLATFORM == "huggingface":
            cheque1_content = cheque1_response
            cheque2_content = cheque2_response
        elif PLATFORM == "mistral":
            cheque1_content = str(cheque1_response)
            cheque2_content = str(cheque2_response)
        print(1)
        print(f"CHEQUE1: {cheque1_content}")
        print(f"CHEQUE2: {cheque2_content}")
        
        # if cheque1_content:
        #     cheque1_content = clean_amount_field(cheque1_content)
        # if cheque2_content:
        #     cheque2_content = clean_amount_field(cheque2_content)
        print(2)
        # if cheque1_content:
        #     cheque1_content = add_age_in_days(cheque1_content)
        # if cheque2_content:
        #     cheque2_content = add_age_in_days(cheque2_content)
        # print(3)
        # if cheque1_content:
        #     cheque1_content = compare_amount(cheque1_content)
        # if cheque2_content:
        #     cheque2_content = compare_amount(cheque2_content)
        print(4)
# THIS IS THE PROBLEM
        cheque1_data = ""
        cheque2_data = ""
        
        # print(f"CHEQUE1: {cheque1_content}")
        # print(f"CHEQUE2: {cheque2_content}")
        if isinstance(cheque1_content, dict) and isinstance(cheque2_content, dict):
            print("COND1")
            cheque1_data = cheque1_content
            cheque2_data = cheque2_content
        
        elif PLATFORM == "nvidia" or PLATFORM == "huggingface":
            print("COND2")
            cheque1_data = json.loads(cheque1_response)
            cheque2_data = json.loads(cheque2_response)
        else:
            print("COND3")
            cheque1_data = json.loads(cheque1_content.replace("'", "\""))
            cheque2_data = json.loads(cheque2_content.replace("'", "\"")) 
        

        print(5)
        for key in cheque1_data.keys():
            if key in ['bank_name']:
                if cheque1_data[key].strip().lower() == cheque2_data[key].strip().lower():
                    comparison_result[key] = "Matching"
                else:
                    comparison_result[key] = f"Not Matching: {cheque1_data[key]} != {cheque2_data[key]}"
            elif key == 'amount':
                if cheque1_data[key] == cheque2_data[key]:
                    comparison_result[key] = "Matching"
                else:
                    difference = abs(cheque1_data[key] - cheque2_data[key])
                    comparison_result[key] = f"Not Matching: {cheque1_data[key]} != {cheque2_data[key]} (Difference: {difference})"
            elif key == 'date':
                normalized_date1 = normalize_date(cheque1_data[key])
                normalized_date2 = normalize_date(cheque2_data[key])
                if normalized_date1 == normalized_date2:
                    comparison_result[key] = "Matching"
                else:
                    comparison_result[key] = f"Not Matching: {cheque1_data[key]} != {cheque2_data[key]}"
            else:
                if cheque1_data[key] == cheque2_data[key]:
                    comparison_result[key] = "Matching"
                else:
                    comparison_result[key] = f"Not Matching: {cheque1_data[key]} != {cheque2_data[key]}"

            # del comparison_result["amountSNComparison"]
        
        #     #added extra for sinature comparison

        # Signature comparison using updated prompt
        signature_result = cheque_signature_compare_llama4(
        new_image,
        reference_image,
        Compare(object_ids=[object_id_1, object_id_2], function_name="cheque_signature_compare_llama4")
        )
        
        # Extract similarity score and apply threshold
        score = signature_result.get("signature_similarity_score", 0)

        if score >= 95:
            match_status = "Signatures Match"
        elif score < 90:
            match_status = "Signatures Do Not Match"
        else:
            match_status = "Review Required"
        
        # Adding signature comparison result to the final comparison result
        # comparison_result["signature_similarity_score"] = score
        comparison_result["signature_match"] = match_status
        # comparison_result["signature_reason"] = signature_result.get("reason", "")





        return cheque1_data, cheque2_data, comparison_result
    except json.JSONDecodeError:
        print(f"COMPARISON: {comparison_result}")
        print("Error decoding JSON content final")
        return {}, {}, {}


def cheque_signature_compare_llama4(new_image, reference_image, compare: Compare):


    if PLATFORM == "nvidia":
        api_key = NVIDIA_KEY
        max_tokens=512
        temperature=1.00 
        top_p=1.00
        stream=False

        with open(new_image, "rb") as f:
            image1_b64 = base64.b64encode(f.read()).decode()

        with open(reference_image, "rb") as f:
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



        payload = {
            "model": NVIDIA_MODEL_LLAMA4,
            "messages": [
                {
                    "role": "user",
                    "content": f"""
                        Provided two bank check images:
                        <img src="data:image/png;base64,{image1_b64}" />
                        <img src="data:image/png;base64,{image2_b64}" />
                        Focus only on the handwritten signature areas in both cheques. Ignore other elements such as bank name, amount, layout, printed text, or stamps.

                        Your task:
                        - Compare the handwriting style, stroke pattern, slant, and curvature of the signatures.
                        - Determine if the signatures belong to the same person.
                        - Be strict in identifying differences in signature style and identity.
                        - Do not consider similarities in cheque layout or printed content.

                        Return a JSON response in the following format:
                        {json.dumps(result_format)}

                        Only return the JSON. Do not include any additional explanation or text.
                        Example:
                        {json.dumps(result_example)}
                        """
                }
            ],
            "max_tokens": max_tokens,
            "temperature": temperature,
            "top_p": top_p,
            "stream": stream
        }

        start_time = time.time()
        response = requests.post(INVOKE_URL_NVIDIA, headers=headers, json=payload)
        end_time = time.time()

        if stream:
            for line in response.iter_lines():
                if line:
                    print(line.decode("utf-8"))
        else:
            content = response.json()
            jsonString = content['choices'][0]['message']['content']
            data = extract_json_from_string(jsonString)

            # jsonObject = json.loads(jsonString)
            # execution_time = end_time - start_time
            return data
    elif PLATFORM == "mistral":
        try:
            file_1_name = get_attachment_name(compare.object_ids[0])
            file_2_name = get_attachment_name(compare.object_ids[1])
            file_path_1 = os.path.join(attachments_folder, file_1_name)
            file_path_2 = os.path.join(attachments_folder, file_2_name)
            response = mistral_infer_2(prompt=cheque_signature_compare_prompt, file_path_1=file_path_1, file_path_2=file_path_2)
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Mistral_infer signature: {e}")
    elif PLATFORM == "huggingface":
        try:
            file_1_name = get_attachment_name(compare.object_ids[0])
            file_2_name = get_attachment_name(compare.object_ids[1])
            file_path_1 = os.path.join(attachments_folder, file_1_name)
            file_path_2 = os.path.join(attachments_folder, file_2_name)
            response = huggingface_infer_2(prompt=cheque_signature_compare_prompt, filepath1=file_path_1, filepath2=file_path_2)
            withId = {
                "response": response,
                "file_name_1": file_1_name,
                "file_name_2": file_2_name,
                "object_id_1": compare.object_ids[0],
                "object_id_2": compare.object_ids[1]
            }
            return withId
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Huggingface_infer signature: {e}")
    else:
        return {"message": "Incorrect platform. Use nvidia, huggingface or mistral"}

async def verify_sharecert_seal_llama4(image1_path, object_id):

    if PLATFORM == "nvidia":

        api_key = NVIDIA_KEY
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
            "model": NVIDIA_MODEL_LLAMA4,
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
        response = requests.post(INVOKE_URL_NVIDIA, headers=headers, json=payload)
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
    elif PLATFORM == "mistral":
        try:

            extract_model = ExtractModel(platform="mistral", object_id=object_id)
            response = mistral_infer_1(extract_model=extract_model, prompt=sharecert_seal_prompt)
            return response
        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Mistral_infer: {e}")
    elif PLATFORM == "huggingface":
        try: 
            response = await huggingface_infer_1(image1_path, prompt=sharecert_seal_prompt)
            return response


        except httpx.RequestError as e:
            raise HTTPException(status_code=502, detail=f"Huggingface_infer: {e}") 
    else:
        return {"message": "Incorrect platform. Use nvidia, huggingface or mistral"}






def clean_mongo_doc(doc):
    """Convert ObjectId and any nested ObjectId to string."""
    for key, value in doc.items():
        if isinstance(value, ObjectId):
            doc[key] = str(value)
        elif isinstance(value, list):
            doc[key] = [str(v) if isinstance(v, ObjectId) else v for v in value]
        elif isinstance(value, dict):
            doc[key] = clean_mongo_doc(value)
    return doc
