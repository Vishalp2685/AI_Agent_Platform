from google import genai
from google.genai import types
from dotenv import load_dotenv
import os
from database.curd import save_message_to_db
from schemas import Role,ToolRequest
from mcps import manager

load_dotenv()

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')

client = genai.Client(api_key = GEMINI_API_KEY)


async def tools():
    tool_list = []

    for tool in await manager.list_tools():
        tool_list.append(
            {
                "name": tool.name,
                "description": tool.description,
                "inputSchema": tool.input_schema
            }
        )
    return tool_list


async def   get_response_from_gemini(data,doc_context:list[str],history = [])->dict:
    tool_list = await tools()
    history = [
        types.Content(
            role=chat.role.value,
            parts=[types.Part(text=chat.message)]
        )
        for chat in history
    ]

    data.user_message = f"Document Context: {doc_context} \n" + "User Message: " + data.user_message
    
    try:
        chat = client.chats.create(
        model = data.model_name,
        history=history,
        config={
            'tools':tool_list
        }
        )
        gemini = chat.send_message(data.user_message)
     
        count = 1
        
        while gemini.function_calls and count < 15:
            tool_name = gemini.function_calls[0].name
            print(f"Executed {tool_name} tool")
            arguments = gemini.function_calls[0].args
            tool = ToolRequest(
                tool_name=tool_name,
                arguments=arguments
            )
            response = await manager.call_tool(tool=tool)
            formated_response = f"Tool call response status: {response.status}, data: {response.data}"
            gemini = chat.send_message(formated_response)
            count += 1

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
    