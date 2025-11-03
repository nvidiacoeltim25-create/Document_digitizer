import base64
import json
from utils.constants import HUGGINGFACE_KEY, HUGGINGFACE_MODEL
from huggingface_hub import InferenceClient
import os
import requests

async def huggingface_infer_1(filepath: str, prompt: str) -> str:
    """
    Describe an image using a Hugging Face Vision model.

    Parameters:
        filepath (str): Path to the local image file.
        prompt (str): Instruction or question about the image.
        api_key (str): Hugging Face API key.
        model (str): Model name (default is LLaMA 3.2 Vision Instruct).

    Returns:
        str: The model's response.
    """
    modell = HUGGINGFACE_MODEL

    # Load and encode the image
    with open(filepath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a data URI
    data_uri = f"data:image/jpeg;base64,{encoded_image}"

    if modell == "accounts/fireworks/models/llama4-maverick-instruct-basic":
        API_URL = "https://router.huggingface.co/fireworks-ai/inference/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_KEY}",
        }
    elif modell == "meta-llama/Llama-3.2-11B-Vision-Instruct":
        API_URL = "https://router.huggingface.co/hf-inference/models/meta-llama/Llama-3.2-11B-Vision-Instruct/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_KEY}",
        }

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()
    
    
    response = query({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri
                        }
                    }
                ]
            }
        ],
        "model": modell, ## MAIN MODEL
        # "model": "meta-llama/Llama-3.2-11B-Vision-Instruct"
        "logprobs": True
    })
    # print(response)

    return response["choices"][0]["message"]["content"]


def huggingface_infer_llama3_2(filepath: str, prompt: str) -> str:
    """
    Describe an image using a Hugging Face Vision model.

    Parameters:
        filepath (str): Path to the local image file.
        prompt (str): Instruction or question about the image.
        api_key (str): Hugging Face API key.
        model (str): Model name (default is LLaMA 3.2 Vision Instruct).

    Returns:
        str: The model's response.
    """
    # Load and encode the image
    with open(filepath, "rb") as image_file:
        encoded_image = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a data URI
    data_uri = f"data:image/jpeg;base64,{encoded_image}"

    API_URL = "https://router.huggingface.co/together/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_KEY}",
    }

    def query(payload):
        API_URL = "https://router.huggingface.co/together/v1/chat/completions"
        headers = {
            "Authorization": f"Bearer {HUGGINGFACE_KEY}",
        }

        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    response = query({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri
                        }
                    }
                ]
            }
        ],
        "model": "meta-llama/Llama-3.2-90B-Vision-Instruct"
    })

    print(response)
    return response["choices"][0]["message"]


def huggingface_infer_2(filepath1: str, prompt: str, filepath2) -> str:
    print(filepath1)
    print(filepath2)
    print(prompt)
    """
    Describe an image using a Hugging Face Vision model.

    Parameters:
        filepath (str): Path to the local image file.
        prompt (str): Instruction or question about the image.
        api_key (str): Hugging Face API key.
        model (str): Model name (default is LLaMA 3.2 Vision Instruct).

    Returns:
        str: The model's response.
    """
    # Load and encode the image
    with open(filepath1, "rb") as image_file:
        encoded_image1 = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a data URI
    data_uri1 = f"data:image/jpeg;base64,{encoded_image1}"
    # Load and encode the image

    with open(filepath2, "rb") as image_file:
        encoded_image2 = base64.b64encode(image_file.read()).decode("utf-8")

    # Create a data URI
    data_uri2 = f"data:image/jpeg;base64,{encoded_image2}"


    API_URL = "https://router.huggingface.co/fireworks-ai/inference/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {HUGGINGFACE_KEY}",
    }

    def query(payload):
        response = requests.post(API_URL, headers=headers, json=payload)
        return response.json()

    response = query({
        "messages": [
            {
                "role": "user",
                "content": [
                    {
                        "type": "text",
                        "text": prompt
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri1
                        }
                    },
                    {
                        "type": "image_url",
                        "image_url": {
                            "url": data_uri2
                        }
                    }
                ]
            }
        ],
        "model": "accounts/fireworks/models/llama4-maverick-instruct-basic"
    })
    print(response)
    json_response = json.loads(response["choices"][0]["message"]['content'])
    return json_response

 

def huggingface_infer(prompt: str) -> str:
    # Initialize the client
    client = InferenceClient(provider="auto", api_key=HUGGINGFACE_KEY)

    # Send the request
    completion = client.chat.completions.create(
        model="meta-llama/Llama-3.3-70B-Instruct",
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt}
                ]
            }
        ],
    )

    return completion.choices[0].message.content