import base64
import zipfile
import io
import os

def decode_and_extract_zip(base64_string, output_folder="extracted_attachments"):
    # Decode the base64 string into bytes
    zip_data = base64.b64decode(base64_string)

    # Create a buffer from the decoded bytes
    zip_buffer = io.BytesIO(zip_data)

    # Extract the zip contents
    with zipfile.ZipFile(zip_buffer, "r") as zip_ref:
        os.makedirs(output_folder, exist_ok=True)
        zip_ref.extractall(output_folder)
        print(f"Extracted files to: {output_folder}")
        print("Extracted files:", zip_ref.namelist())

# decode_and_extract_zip(email_response["attachments_zip_b64"])