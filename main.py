from fastapi import FastAPI, File, UploadFile, HTTPException
import asyncio
from schemas import ModelResponse,ModelResponsePayload,Chats,Role,Document,DocsResponsePayload
from database.curd import (is_session_id_present,save_message_to_db,get_all_chat_session_ids,
                get_session_chats,save_session_id,save_doc_data,save_embeddings,search_relavent_chunks
                )
from database.database import test_db_connection
from Utils.utils import generate_random_string
from llms.gemini import get_response_from_gemini
from redis.asyncio import Redis
from contextlib import asynccontextmanager
from datetime import datetime,timezone 
from pydantic import TypeAdapter
from fastapi.middleware.cors import CORSMiddleware
from pathlib import Path
from typing import Annotated
import os
from rag.embeddings import embed
from rag.extractor import extract_text_from_pdf
from rag.chunker import create_chunks
from mcps import manager

adapter = TypeAdapter(list[Chats])

UPLOAD_DIR = Path('uploads')
UPLOAD_DIR.mkdir(parents=True,exist_ok=True)
ALLOWED_MIME = 'application/pdf'


redis = Redis(
    host = 'localhost',
    port = 6379,
    decode_responses=True
)

@asynccontextmanager
async def lifespan(app:FastAPI):
    try:
        await redis.ping()
        print("Connected to redis...")
    except Exception as e:
        print("Failed to connect the redis server, check if the redis server is running on port 6379")
        raise SystemExit(1)
    # Checking the db 
    print("Connecting to db.....")
    if test_db_connection():
        print("Connected to db")
    else:
        print("Failed to connect to db")
        raise SystemExit(1) 
    # Initializing the mcps
    await manager.initalize()
    # print(manager)
    yield
    await redis.close()

app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://127.0.0.1:5500",
        "http://localhost:5500",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)   

@app.post('/chat/get_response',response_model=ModelResponsePayload)
async def get_response(data:ModelResponse):
    '''
    Use this endpoint to save and get the response in one endpoint
    '''
    # check if chat_history of chat_session exist
    chat_history_json = await redis.get(f"chat:session:{data.chat_session_id}")

    if chat_history_json: # if exist convert it to Chats type
        chat_history = adapter.validate_json(chat_history_json)
    else: # else get the history form db
        chat_history = get_session_chats(data.chat_session_id)
    
    user_message_vector = embed(data.user_message)
    context = search_relavent_chunks(user_message_vector,data.chat_session_id)

    # save user message to db
    user,response_data = await asyncio.gather(save_message_to_db(data),
                get_response_from_gemini(data,doc_context=context,history=chat_history))
    
    if user['status'] and response_data['status']:
        chat_history.extend([Chats(
            role = Role.user,
            message = data.user_message,
            model_used = data.model_name,
            sent_on = datetime.now(timezone.utc) 
        ),
        Chats(
            role = Role.model,
            message = response_data['response'],
            model_used =  data.model_name,
            sent_on = datetime.now(timezone.utc)
        )])
        
        await redis.set(
            f"chat:session:{data.chat_session_id}",adapter.dump_json(chat_history),
            ex=86400
            ) 
        return ModelResponsePayload(
            status=True,
            model_answer=response_data['response'],
            chat_session_id= data.chat_session_id
        )
    else:
        return ModelResponsePayload(
            chat_session_id=data.chat_session_id,
            comments='Failed to either save the user_data or get the response from model'
        )

@app.get('/chat/create_new_session')
async def create_new_session():
    while True:
        session_id = generate_random_string()
        present = is_session_id_present(session_id)
        if not present:
            if save_session_id(session_id):
                return session_id
            else:
                raise HTTPException(status_code=500, detail='failed to save the session id to db.')

@app.get('/get_all_sessions/',response_model=list)
async def get_sessions():
    chat_sessions = get_all_chat_session_ids()
    return chat_sessions

@app.get('/chat/get_chats/{session_id}',response_model=list[Chats])
async def get_chats(session_id):
    chats = get_session_chats(session_id)
    formated_chats = adapter.dump_json(chats)
    await redis.set(f"chat:session:{session_id}",formated_chats,ex = 86400)
    return chats

@app.get('/clear_redis')
async def clear_redis():
    await redis.flushall(asynchronous=True)
    return True

@app.post('/documents/upload/',response_model=DocsResponsePayload)
async def parse_document(session_id:str,file: Annotated[UploadFile, File(description="The document to upload")]):
    '''
    For now this endpoint will allow to upload the document,save it to system and save the 
    embeddigs to the db.
    To get the response call the get response function. 
    '''
    if file.content_type != ALLOWED_MIME:
            raise HTTPException(
                status_code=400,
                detail="Invalid file type. Only PDF files are allowed."
            )

    if not file.filename:
        raise HTTPException(status_code=400, detail="filemame missing")
    
    if not is_session_id_present(session_id):
        raise HTTPException(status_code=400, detail='Invalid session_id')

    safe_filename = generate_random_string(length=16)
    dest_path = UPLOAD_DIR/safe_filename

    try:
        with open(dest_path, 'wb') as buffer:
            while chunk := await file.read(1024*1024):
                buffer.write(chunk)

        metadata = Document(
        session_id=session_id,
        file_name=safe_filename,
        file_loc=str(dest_path)
        )
        
        saved = save_doc_data(metadata)
        if not saved['status']:
            raise HTTPException(status_code=500, detail='Failed to save metadata in db')
        print(saved)
        print("-------------------------------------------------") 
        # creating the vectors for thr text from the document.
        text = extract_text_from_pdf(file_path=dest_path)
       
        chunks = create_chunks(text=text)
        
        embeddings = embed(chunks)
        response = save_embeddings(vectors = embeddings,document_id= saved['file_id'],chunks=chunks)
        if not response['status']:
            raise HTTPException(status_code=500, detail=f"failed to save embeddings: {response['comments']}")

    except Exception as e:
        if dest_path.exists():
            dest_path.unlink()
        raise HTTPException(status_code=500, detail=f"failed to save file: {str(e)}")
    finally:
        await file.close()
    
    return DocsResponsePayload(
        status=True,
        file_path=str(dest_path),
        file_name=safe_filename,
        file_id = saved['file_id']
    )

@app.get('/test/chat/')
def test_chunks(message:str,session_id:str):
    mess_vector = embed(message)
    return search_relavent_chunks(mess_vector,session_id)


@app.get('/list_tools')
async def get_tools():
    tools = await manager.list_tools()
    return len(tools)