from pydantic import BaseModel
from enum import Enum
from datetime import datetime


class Role(str,Enum):
    model = 'model'
    user = 'user'

class Models(str,Enum):
    gemma4_26B = 'gemma-4-26b-a4b-it'
    gemma4_31B = 'gemma-4-31b-it'

class ModelResponse(BaseModel):
    model_name: Models
    chat_session_id: str
    user_message: str
    role: Role = 'user'

class ResponsePayload(BaseModel):
    status: bool = False
    comments: str|None = None

class ModelResponsePayload(ResponsePayload):
    model_answer: str|None = None
    chat_session_id: str|None = None

class Message(BaseModel):
    chat_session_id: str
    message: str
    role: Role
    model_used: Models

class Chats(BaseModel):
    role: Role
    message:str
    model_used:Models
    sent_on:datetime

class ChatResponse(BaseModel):
    User: Chats
    AI: Chats

class Document(BaseModel):
    session_id: str
    file_name: str
    file_loc: str

class DocsResponsePayload(ResponsePayload):
    status: bool
    file_path: str
    file_name: str
    file_id: int

class Embeddings(BaseModel):
    document_id: int
    embeddings: float
    chunk_text: str