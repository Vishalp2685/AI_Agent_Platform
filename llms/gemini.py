from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from database.curd import save_message_to_db
from schemas import Role
load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key = GEMINI_API_KEY)

async def   get_response_from_gemini(data,history = [])->dict:
    history = [
        types.Content(
            role=chat.role.value,
            parts=[types.Part(text=chat.message)]
        )
        for chat in history
    ]
    
    try:
        chat = client.chats.create(
        model = data.model_name,
        history=history
        )
        gemini = chat.send_message(data.user_message)
        data.user_message = gemini.text
        data.role = Role.model
        saved = await save_message_to_db(data)
        if saved['status']:
            return {'status':True,'response':gemini.text}
        else:
            print('Failed to save response to db')
            return {'status':False,'response':""}
    except Exception as e:
        print(f"[Model.py(get_response_from_gemini)][Error]: {e}")
        return {'status':False, 'response': None}
    
