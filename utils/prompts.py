import json
import utils.exampleOutputs as examples
from utils.exampleOutputs import result_example, result_format

extract_data_prompt = f"""
    You are a document verification system having the permission to extract data from all kinds of documents
        Extract data from it and provide it in a JSON format.
        Don't provide anything else in the output except the JSON.
        Here are example outputs {json.dumps(examples.output_example1)} {json.dumps(examples.output_example2)} {json.dumps(examples.output_example3)} {json.dumps(examples.output_example4)} {json.dumps(examples.output_example5)} {json.dumps(examples.output_example6)}
"""

extract_text_prompt = f"""
                Extract the text from the given image according to this JSON format: {json.dumps(examples.json_schema7)}
                Don't provide anything else in the output except the JSON
                Format of date should be: "YYYY-MM-DD"
                amountNumber should contain the amount written after dollar symbol
            
                {json.dumps(examples.output_example7)}
        """

sharecert_seal_prompt = f"""
            Provided an image
            Identify if it contains medallion signature or not
            Respond yes medallion signature is present otherwise no 
            Don't provide anything else in the output
        """

# cheque_signature_compare_prompt = f"""
#     You are a signature verification system. Provided below are two bank cheque images
#     Focus only on the handwritten signature areas in both cheques. Ignore other elements such as bank name, amount, layout, printed text, or stamps.

#     Your task:
#     - Compare the handwriting style, stroke pattern, slant, and curvature of the signatures.
#     - Determine if the signatures belong to the same person.
#     - Be strict in identifying differences in signature style and identity.
#     - Do not consider similarities in cheque layout or printed content.
#     and provide comparison result
#     Use the below explanations
#     {json.dumps(result_format)}
#     Ensure that your responses are formatted correctly as JSON and contain only the necessary information requested.
#     Do not include any additional text or explanations or anything else outside of the JSON format.
#     example response format:
#     Do not add anything other than the response format given below.
#     {json.dumps(result_example)}
#     Do not provide anything else other than the json
# """
cheque_signature_compare_prompt = f"""
You are a signature verification system. Provided below are two bank cheque images
    Focus only on the handwritten signature areas in both cheques. Ignore other elements such as bank name, amount, layout, printed text, or stamps.

    Your task:
    - Compare the handwriting style, stroke pattern, slant, and curvature of the signatures.
    - Determine if the signatures belong to the same person.
    - Be strict in identifying differences in signature style and identity.
    - Do not consider similarities in cheque layout or printed content.
    and provide comparison result
    Use the below explanations
    {json.dumps(result_format)}
    Ensure that your responses are formatted correctly as JSON and contain only the necessary information requested.
    Do not include any additional text or explanations or anything else outside of the JSON format.
    example response format:
    Do not add anything other than the response format given below.
    {json.dumps(result_example)}
    Do not provide anything else other than the json
"""