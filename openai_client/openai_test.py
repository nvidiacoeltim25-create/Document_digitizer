import os
import sys

import base64
from openai import OpenAI
from llm_confidence.logprobs_handler import LogprobsHandler
from utils.constants import OPENAI_API_KEY, OPENAI_MODEL


def infer_openai_2(filepath, prompt, model):
    client = OpenAI(api_key=OPENAI_API_KEY)

    # Initialize the LogprobsHandler
    logprobs_handler = LogprobsHandler()

    with open(filepath, "rb") as image_file:
        b64_imagee = base64.b64encode(image_file.read()).decode("utf-8")

    response = client.chat.completions.create(
        model=model,
        # max_tokens=300,
        messages=[
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": {"url": f"data:image/png;base64,{b64_imagee}"}},
                ],
            }
        ],
        logprobs=True,
        # response_format={'type': 'json_object'}
    )
    # print(response.choices[0])
    # Extract the log probabilities from the response
    response_logprobs = response.choices[0].logprobs.content if hasattr(response.choices[0], 'logprobs') else []

    # Format the logprobs from OpenAI
    logprobs_formatted = logprobs_handler.format_logprobs(response_logprobs)

    # Process the log probabilities to get confidence scores
    confidence = logprobs_handler.process_logprobs(logprobs_formatted)

    # Print the confidence scores
    print("CONFIDENCE:", confidence)
    # print(f"FILE PATH: {filepath}: \n", response.choices[0].message.content)
    return response.choices[0].message.content


def genCustomFieldsPrompt1(fields_list):
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


# Define the folder path
folder_path = '/home/ujjwal-ltim/ujjwal/computershare/email_st/customer_sample_docs'

# Define the prompt and model to be used
prompt = genCustomFieldsPrompt1(fields_list=["fitting number","qty","D1 duct dia","L1 duct length","D1 ring type","D2 ring type", "remarks"])
model = "gpt-4o"
output_file = 'output_results2.txt'

# Open the output file for writing
with open(output_file, 'w') as out_file:
    for filename in os.listdir(folder_path):
        filepath = os.path.join(folder_path, filename)
        if os.path.isfile(filepath):
            try:
                result = infer_openai_2(filepath, prompt, model)
                out_file.write(f"FILE: {filename}\nRESULT:\n{result}\n\n")
            except Exception as e:
                out_file.write(f"FILE: {filename}\nERROR: {str(e)}\n\n")


