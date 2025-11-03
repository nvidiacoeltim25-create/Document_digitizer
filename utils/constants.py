from pathlib import Path
import json
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Base directory assumed to be the current working directory
BASE_DIR = Path.cwd()

# Define relative paths
attachments_folder = BASE_DIR / "attachments_db"
JWT_KEY_FILE_PATH = BASE_DIR / "jwt_secret_key.txt"
config_file_path = BASE_DIR / "config.json"
MCP_TOOLS_PATH = BASE_DIR / "mcp_client" / "dd_mcp_tools.py"

# Load config
with open(config_file_path, 'r') as file:
    config = json.load(file)

# Constants
MONGO_URL = "mongodb://localhost:27017/"
PLATFORMS = ["nvidia", "mistral", "huggingface"]
MODELS = ["meta/llama-3.2-90b-vision-instruct", "meta/llama-3.2-11b-vision-instruct"]
PLATFORM = config["platform"]

PORT = 8003
MCP_PORT = 8002
FACE_SIGN_ML_PORT = 8087

FACE_SIGN_COMPARE_BASEURL = f"http://127.0.0.1:{FACE_SIGN_ML_PORT}"

# Load from .env
NVIDIA_KEY = os.getenv("NVIDIA_KEY")
NVIDIA_API_KEY_MCP = os.getenv("NVIDIA_API_KEY_MCP")
HUGGINGFACE_KEY = os.getenv("HUGGINGFACE_KEY")
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
OPENAI_API_KEY_MCP = os.getenv("OPENAI_API_KEY_MCP")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")



NVIDIA_MODEL_LLAMA4 = 'meta/llama-4-maverick-17b-128e-instruct'
MISTRAL_MODEL = "mistral-small-latest"
OPENAI_MODEL = "gpt-4o"

HUGGINGFACE_MODEL = config["huggingface_model"]
NVIDIA_MODEL = config["nvidia_model"]

INVOKE_URL_NVIDIA = "https://integrate.api.nvidia.com/v1/chat/completions"
EMAIL_FETCH_BASEURL = config["fetch_email_link"]

FILE_TYPES = [
    "passport", "driver's license", "cheque", "corporate resolution",
    "PAN card", "adhaar card", "shareholder's certificate",
    "affidavit", "permashield"
]

# {
#     "version": "1.0.1",
#     "platform": "huggingface",
#     "nvidia_model": "meta/llama-3.2-90b-vision-instruct",
#     "fetch_email_link": "",
#     "LINK": "",
#     "huggingface_model": "accounts/fireworks/models/llama4-maverick-instruct-basic"
# }