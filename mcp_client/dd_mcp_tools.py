import os
import sys
from mcp.server.fastmcp import FastMCP
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))



from mcp.server.fastmcp import FastMCP
from models.models import (
    AttachmentIDs, ChatRequest, Config, CustomExtractModel, FetchEmailRequest,
    GeneralEmailInput, Response, Compare, CompareChequesRequest, CompareModel,
    EmailIDs, EmailRequest, ExtractModel, JsonList, ObjectIDs, SaveDataModel
)
from utils.core_features import (
    clearAllEmailsUtil, compareChequesUtil, compareFaceSignUtil, deleteAttachmentsUtil,
    deleteEmailsUtil, extractCustomTabularDataUtil, extractDataUtil, fetchEmailUtil,
    generateEmailGeneralUtil, generateEmailSchemaUtil, getAllFilesInfoUtil,
    getAllFilesZipUtil, getConfigUtil, getFilesByIdUtil, getReferenceDocsUtil,
    getSavedDataUtil, mcpChatUtil, saveDataUtil, sendEmailUtil, updateConfigUtil,
    uploadFilesUtil, verifyUtil, rag_chatbot
)

mcp = FastMCP("API Tools")

@mcp.tool()
async def get_config():
    """Fetch the current configuration settings."""
    return await getConfigUtil()

@mcp.tool()
async def update_config(platform: str, model: str, fetch_email_active: bool, fetch_email_link: str):
    """Update the configuration settings."""
    config = Config(platform=platform, model=model, fetch_email_active=fetch_email_active, fetch_email_link=fetch_email_link)
    return updateConfigUtil(config)

@mcp.tool()
async def get_files_by_id(object_ids: list):
    """Retrieve files by their object IDs."""
    return await getFilesByIdUtil(ObjectIDs(object_ids=object_ids))

@mcp.tool()
async def get_all_files_zip():
    """Download all files as a ZIP archive."""
    return await getAllFilesZipUtil()

@mcp.tool()
async def get_all_files_info():
    """Get metadata and file paths of all files."""
    return await getAllFilesInfoUtil()

@mcp.tool()
async def get_reference_docs():
    """Retrieve reference documents from the database."""
    return getReferenceDocsUtil()

@mcp.tool()
async def delete_attachments(attachment_ids: list):
    """Delete attachments by their object IDs."""
    return await deleteAttachmentsUtil(AttachmentIDs(attachment_ids=attachment_ids))

@mcp.tool()
async def delete_emails(email_ids: list):
    """Delete emails by their IDs."""
    return await deleteEmailsUtil(EmailIDs(email_ids=email_ids))

@mcp.tool()
async def clear_emails():
    """Clear all emails from the database."""
    return await clearAllEmailsUtil()

@mcp.tool()
async def extract_data(platform: str, object_id: str):
    """Extract structured data from documents."""
    return await extractDataUtil(ExtractModel(platform=platform, object_id=object_id))

@mcp.tool()
async def extract_custom_tabular(object_ids: list, custom_fields: list):
    """Extract custom tabular data from documents."""
    return await extractCustomTabularDataUtil(CustomExtractModel(ObjectIDs=object_ids, customFields=custom_fields))

@mcp.tool()
async def generate_email(json_data: list):
    """Generate a consolidated email from JSON data."""
    return await generateEmailSchemaUtil(JsonList(data=json_data))

@mcp.tool()
async def generate_email_general(object_ids: list, action: str, result: list):
    """Generate a general email from provided input."""
    return await generateEmailGeneralUtil(GeneralEmailInput(object_ids=object_ids, action=action, result=result))

@mcp.tool()
async def send_email(recipient_email: str, subject: str, plain_text: str, html_content: str):
    """Send an email to the specified recipient."""
    return await sendEmailUtil(EmailRequest(recipient_email=recipient_email, subject=subject, plain_text=plain_text, html_content=html_content))

@mcp.tool()
async def compare_cheques(object_id_1: str, object_id_2: str):
    """Compare two cheque documents."""
    return await compareChequesUtil(CompareChequesRequest(object_id_1=object_id_1, object_id_2=object_id_2))

@mcp.tool()
async def verify(function_name: str, object_ids: list):
    """Verify signature or seal in a document."""
    return await verifyUtil(Compare(function_name=function_name, object_ids=object_ids))

@mcp.tool()
async def fetch_emails(email_id: str, password: str):
    """Fetch emails using provided credentials."""
    return await fetchEmailUtil(FetchEmailRequest(email_id=email_id, password=password))

@mcp.tool()
async def save_data(function: str, object_ids: list, data: dict):
    """Save extracted or processed data to the database."""
    return await saveDataUtil(SaveDataModel(function=function, object_ids=object_ids, data=data))

@mcp.tool()
async def get_saved_data(data_id: str):
    """Retrieve saved data by its ID."""
    return await getSavedDataUtil(data_id)

@mcp.tool()
async def mcp_chat(message: str):
    """Chat with the MCP system using a prompt."""
    return await mcpChatUtil(ChatRequest(message=message))

@mcp.tool()
async def compare_face_sign(function: str, object_id_1: str, object_id_2: str):
    """Compare face or signature images using ML. For face comparison pass "face" in function and for signature comparison pass "sign" in function"""
    return await compareFaceSignUtil(CompareModel(function=function, object_id_1=object_id_1, object_id_2=object_id_2))

@mcp.tool()
async def rag_chatbot_tool(query: str) -> str:
    """Run RAG chatbot on a user query and return the response for all the queries without file id or object id."""
    return await rag_chatbot(query)

if __name__ == "__main__":
    print("Strating dd mcp server")
    mcp.run(transport="stdio")