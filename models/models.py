from typing import Dict, List
from pydantic import BaseModel, EmailStr

class EmailItem(BaseModel):
    email: str
    subject: str
    body: str
    attachments_zip_b64: str

class FetchEmailResponse(BaseModel):
    emails: List[EmailItem]

class Response(BaseModel):
    response: str

class ObjectIDs(BaseModel):
    object_ids: List[str]

class DocumentModel(BaseModel):
    ObjectId: str
    file_name: str

class AttachmentIDs(BaseModel):
    attachment_ids: List[str]

class EmailIDs(BaseModel):
    email_ids: List[str]

class DocumentID(BaseModel):
    document_id: str

class Query(BaseModel):
    question: str
    data: dict
    
class JsonList(BaseModel):
    data: List[Dict]

class EmailRequest(BaseModel):
    recipient_email: EmailStr
    subject: str
    plain_text: str
    html_content: str

class CompareChequesRequest(BaseModel):
    object_id_1: str
    object_id_2: str

class Compare(BaseModel):
    function_name: str
    object_ids: list
    # platform: str

class ChatRequest(BaseModel):
    message: str

class CompareModel(BaseModel):
    function: str
    object_id_1: str
    object_id_2: str

class ExtractModel(BaseModel):
    platform: str
    object_id: str

class CustomExtractModel(BaseModel):
    ObjectIDs: List[str]
    customFields: List[str]

class FetchEmailRequest(BaseModel):
    email_id: str
    password: str

class SaveDataModel(BaseModel):
    function: str
    object_ids: List[str]
    data: dict


class Config(BaseModel):
    version: str
    platform: str
    nvidia_model: str
    fetch_email_link: str
    LINK: str
    huggingface_model: str

class GeneralEmailInput(BaseModel):
    object_ids: List[str]
    action: str
    result: List[dict]

# class RagChatbotInput(BaseModel):
#     query: str