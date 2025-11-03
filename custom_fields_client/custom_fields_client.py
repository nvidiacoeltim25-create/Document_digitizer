import os
import sys
from fastapi import Body, FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import uvicorn
import re
import json
import asyncio
from typing import List


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from huggingface_client.hfClient import huggingface_infer_1
from models.models import DocumentModel
from bson import ObjectId
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware


app = FastAPI()

import json
import csv

def json_to_csv(json_string: str, output_file: str):
    """
    Converts a JSON string with a single key containing comma-separated values
    into a CSV file with individual columns.

    Parameters:
    - json_string (str): The JSON string to convert.
    - output_file (str): Path to the output CSV file.
    """
    try:
        data = json.loads(json_string)
        if not data:
            raise ValueError("Empty or invalid JSON data.")

        # Extract headers from the single key
        combined_key = list(data[0].keys())[0]
        headers = combined_key.split(',')

        with open(output_file, mode='w', newline='', encoding='utf-8') as csvfile:
            writer = csv.writer(csvfile)
            writer.writerow(headers)

            for item in data:
                combined_value = item[combined_key]
                row = combined_value.split(',', maxsplit=len(headers)-1)
                writer.writerow(row)

        print(f"CSV file created successfully at: {output_file}")
    except Exception as e:
        print(f"Error converting JSON to CSV: {e}")



def genPrompt(fields_list):
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


def clean_text(input_text: str) -> str:
    input_text = re.sub(r'(\d+)""', r'\1\\"', input_text)
    input_text = re.sub(r'(\d+)"', r'\1\\"', input_text)
    json_match = re.search(r'\[\s*{.*?}\s*\]', input_text, re.DOTALL)
    return json_match.group(0) if json_match else None


from fastapi.responses import FileResponse


@app.post("/add-document-schema/")
async def add_document(doc: DocumentModel):
    try:
        result = tabular_custom_fields_coll.insert_one(doc.dict())
        return {"message": "Document added", "id": str(result.inserted_id)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/get-document-schemas/")
async def get_documents():
    try:
        documents = list(tabular_custom_fields_coll.find())
        # Convert ObjectId to string for JSON serialization
        for doc in documents:
            doc["_id"] = str(doc["_id"])
        return JSONResponse(content=documents)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/extract_custom_tabular/")
async def extract_data(files: List[UploadFile] = File(...), fields: List[str] = Body()):
    mode = 2
    if mode == 1:
        for file in files:
            contents = await file.read()
            with open(file.filename, "wb") as f:
                f.write(contents)

            try:
                model_output = await huggingface_infer_1(file.filename, genPrompt(fields_list=fields))
                cleaned_json = clean_custom_fields_text(model_output)
                cleaned_string = cleaned_json.replace('\\\"', '\"').replace('\\', '')
                # updated_text = re.sub(r'"(\d+)"', r'"\1inches"', cleaned_string)
                # updated_text = re.sub(r'(\d+)"', r'\1inch', cleaned_string)
                converted = re.sub(r'"(\d+)"(?=")', r"'\1inches'", cleaned_string)
                
                # fixed_text = re.sub(r"'(\d+inches)\"'", r'"\1"', converted)
                
                fixed_text = re.sub(r'":\s*\'(\d+inches)\'"', r'": "\1"', converted)



                # cleaner_string = cleaned_string.replace("\"", "inch")
                # cleaner_string2 = cleaner_string.replace("\\", "")
                print(fixed_text)
                return {"response": json.loads(fixed_text)}
                # return {"data": cleaned_json}
                if cleaned_json:
                    csv_filename = f"{os.path.splitext(file.filename)[0]}_output.csv"
                    json_to_csv(cleaned_json, csv_filename)
                    return FileResponse(csv_filename, media_type='text/csv', filename=csv_filename)
                else:
                    return JSONResponse(content={"error": "No valid JSON found"}, status_code=400)
            except Exception as e:
                return JSONResponse(content={"error": str(e)}, status_code=500)
    else:
        for file in files:
            contents = await file.read()
            with open(file.filename, "wb") as f:
                f.write(contents)

                try:
                    model_output = await huggingface_infer_1(file.filename, genCustomFieldsPrompt(fields_list=fields))
                    cleaned_json1 = clean_custom_fields_text(model_output)
                    cleaned_string1 = cleaned_json1.replace('\\\"', '\"').replace('\\', '')

                    confidence_prompt = f"""
                    {str(cleaned_string1)}

                    Add a confidence score from 0 to 100 depicting the correctness of data extracted by the LLM
                    
                    Give only the final json with the confidence score in the response
                    Do not add any text in the response
                    """

                    model_pass_2 = await huggingface_infer_1(file.filename, confidence_prompt)
                    cleaned_json = clean_custom_fields_text(model_pass_2)
                    cleaned_string = cleaned_json.replace('\\\"', '\"').replace('\\', '')
                    print(cleaned_string)
                    return {"response": cleaned_string}
                except Exception as e:
                    return JSONResponse(content={"error": str(e)}, status_code=500)
# from fastapi import Form

# @app.post("/extract/")
# async def extract_data(
#     files: List[UploadFile] = File(...),
#     doc_type_name: str = Form(...),
#     custom_fields: List[str] = Form()
# ):
   

#     if doc_type_name == "string" or doc_type_name == "":
#         fields = custom_fields
#     else:
#          # Fetch fields from MongoDB using doc_type_name
#         doc = tabular_custom_fields_coll.find_one({"doc_type_name": doc_type_name})
#         if not doc:
#             return JSONResponse(content={"error": "doc_type_name not found"}, status_code=404)
#         fields = doc.get("doc_fields", [])
#         print(fields)

#     for file in files:
#         contents = await file.read()
#         with open(file.filename, "wb") as f:
#             f.write(contents)

#         try:
#             model_output = await huggingface_infer_1(file.filename, genPrompt(fields_list=fields))
#             cleaned_json = clean_text(model_output)
#             print(cleaned_json)
#             if cleaned_json:
#                 csv_filename = f"{os.path.splitext(file.filename)[0]}_output.csv"
#                 json_to_csv(cleaned_json, csv_filename)
#                 if os.path.exists(csv_filename):
#                     return FileResponse(csv_filename, media_type='text/csv', filename=csv_filename)
#                 else:
#                     return JSONResponse(content={"error": "CSV file was not created"}, status_code=500)

#             else:
#                 return JSONResponse(content={"error": "No valid JSON found"}, status_code=400)
#         except Exception as e:
#             return JSONResponse(content={"error": str(e)}, status_code=500)



if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8082)
