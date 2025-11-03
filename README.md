# HOW TO RUN

1. Clone this repo

2. Setup conda and run 
You will need 3 python environments named:
- verification
- ddmcpenv
- comparison

install the requirements for each using respective .txt file from conda_envs/
- pip install -r verification.txt
- pip install -r ddmcpenv.txt
- pip install -r comparison.txt

3. Setup mongoDB
https://www.mongodb.com/docs/manual/installation/

4. Create file named .env in root (with apis.py) and add with your keys:
NVIDIA_KEY=
HUGGINGFACE_KEY=
MISTRAL_API_KEY=
OPENAI_API_KEY=


5. run dd using:
sh runDocDig.sh
OR
bash runDocDig.hs

6. Stop the application:
sh stopDD.sh
OR
bash stopDD.hs

7. Access the running apis on:
http://localhost:8003/docs#/


# CHANGELOG

## 0.0.1

### API name change extract_data_nvidia_llama-3.2-90b-vision-instruct -> extract_data

payload = {
  "platform": "huggingface",
  "object_id": "684008bef3a01b34dc80eb19"
}

platform can be "nvidia", "huggingface", "mistral"


## 0.0.2

### API addition

endpoint: /save_data
description: Saves data to database
payload = {
        "function": "",
        "object_ids": [],
        "data": ""
    }
function can be "extract" or "compare"
if function is "extract":
  "object_ids": ["683d85efd056b0707d641405"]
if function is "compare":
  "object_ids": ["683d85efd056b0707d641405", "683e8c736ea8c7cb425a117a"]


## 0.0.3

Config.json
platfroms: "nvidia", "hf", "mistral"
models: "meta/llama-3.2-90b-vision-instruct", "meta/llama-3.2-11b-vision-instruct"
Mistral don't need model name, model name only for nvidia, hf


## 0.0.4

### API addition

endpoint: /compare_face_sign_ML
description: Compare face and signatures from 2 images using ML
payload = {
        "function": "face",
        "object_id_1": "",
        "object_id_2": ""
    }
function can be "face" or "sign"

response = {
  "similarity_score": "0.1497",
  "time_taken": "2.4399 seconds"
}

## 0.0.5

### Added sharable file paths for Deployed machine

access files in db like this after forwarding port 8003:
http://localhost:8003/attachments_db/check4.jpg

## 0.0.6

### API addition

endpoint: /generate_email_general
description: Generate email for any type of data(extraction or comparison)
payload = {
        "object_id_1": "",
        "object_id_2": "",
        "action": "face comparison",
        "result": {}
    }

action: name of the action performed. 
Example: "face comparison", "signature comparison", "shareholder's certificate seal verification", "cheque comparison"

result: dictionary of the response from the action


## 0.0.7

### API addition

endpoint: /delete_emails
description: Clears all emails from DB

type: delete

## 0.0.8

### API update

endpoint: /get_all_files_info/
description:
 1. change in response structure
 2. Added file_type

Sample output:
{
  "685a2610616074ee4e6b7083": {
    "file_type": "cheque",
    "file_name": "382ed7ce-2c4f-4643-ae9b-d7283138e47d.jpg"
  },
  "685a260c616074ee4e6b7080": {
    "file_type": "corporate resolution",
    "file_name": "e52a4987-273c-41e8-8da0-fc72c09a58ac.jpg"
  },
  "685a260a616074ee4e6b707f": {
    "file_type": "passport",
    "file_name": "91e350e5-8087-4f6d-8756-c1625f4cc4b5.jpg"
  },
}

## 0.0.9

### API addition

endpoint: extract_custom_tabular/
description: 
Extract rows from tabular data by passing the column names user wants

Sample Input:
{
  "ObjectIDs": [
    "686e82c2dbd5b464fc55e67b"
  ],
  "customFields": [
    "fitting number", "qty", "part number", "description", "duct dia", "duct length"
  ]
}

customFields: list of strings input from user 

Sample output: 
{
  "response": [
    {
      "686e82c2dbd5b464fc55e67b": [
        {
          "fitting number": "KAZ-K061",
          "qty": "2",
          "part number": "RC04",
          "description": "4\" (101.6) DIA. - STAINLESS STEEL CAST RING",
          "duct dia": "4\" (101.6)",
          "duct length": "",
          "confidence score": 100
        },
        {
          "fitting number": "KA-M013",
          "qty": "3",
          "part number": "RC06",
          "description": "6\" (152.4) DIA. - STAINLESS STEEL CAST RING",
          "duct dia": "6\" (152.4)",
          "duct length": "",
          "confidence score": 100
        }
      ]
    }
  ]
}



## 0.1.0

### API addition

endpoint: delete_attachments/
description: 
Pass a list of object ids you want to delete from the database
THIS ACTION WILL BE IRREVERSIBLE

Sample Input:
{
  "attachment_ids": [
    "686e82c2dbd5b464fc55e67b", "685a2610616074ee4e6b7083"
  ],
}


Sample output: 
{
  "detail": "Attachments deleted successfully"
}


## 0.1.1

### API UPDATE

- Add filename and object ID in certificate signature verify DONE
Endpoint: /verify/

when In payload: function_name: "cheque_signature_compare_llama4"

{
"response": response,
"file_name_1": file_1_name,
"file_name_2": file_2_name,
"object_id_1": compare.object_ids[0],
"object_id_2": compare.object_ids[1]
}

------------------------------------------------------------

- Add filename and object ID in face comparison done
Endpoint: /compare_face_sign_ML
{
"response": response.json(),
"object_id_1": compare_model.object_id_1,
"object_id_2": compare_model.object_id_2,
"file_name_1": get_attachment_name(compare_model.object_id_1),
"file_name_2": get_attachment_name(compare_model.object_id_2)
}

------------------------------------------------------------

- Return data in response when save_data called
Endpoint: /save_data

{
  "message": "SUCCESS: Data saved successfully",
  "data": {
    "function": "extract",
    "object_ids": [
      "686e82c3dbd5b464fc55e67c"
    ],
    "data": {
      "original_name": "Straight Duct - D3 PNG.png"
    },
    "_id": "688ca1746d1d2b4c3a6d3ff4"
  }
}
