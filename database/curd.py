from .database import SessionLocal as sl
from .models import Documents,ChatSessions,ChatMessages,DocumentChunks
from schemas import Document,Message,Embeddings
from sqlalchemy import select
from Utils.utils import format_chats


def save_doc_data(data:Document):
    try:
        doc = Documents(
                session_id=data.session_id,
                file_name=data.file_name,
                file_at=str(data.file_loc),
            )
        with sl() as session:
            session.add(doc)
            session.commit()
            file_id = doc.id
            # file_id = session.scalar(select(Documents.id).where(Documents.session_id == data.session_id,
            #                                           Documents.file_name == data.file_name))
        return {'status':True, 'comments':'Docs data saved to db','file_id':file_id}
    except Exception as e:
        print(f"[Error][curd.py(save_doc_data): {e}]")
        return {'status': False, 'comments':'Failed to save doc data'}
    
def is_session_id_present(session_id: str):
    '''
    Returns True if session id is present
    '''
    with sl() as session:
        id = session.scalar(select(ChatSessions.session_id).where(ChatSessions.session_id == session_id))
    return True if id else False

def save_session_id(session_id: str):
    try:
        with sl() as session:
            session.add(ChatSessions(
                session_id = session_id
            ))
            session.commit()
        return True
    except Exception as e:
        print(f"[Error][db.py(save_session_id): {e}]")

async def save_message_to_db(data:Message)->dict:
    message = ChatMessages(
        chat_session_id = data.chat_session_id,
        message = data.user_message,
        role = data.role,
        model_used = data.model_name
    )

    try:
        with sl() as session:
            session.add(message)
            session.commit()
        return {'status': True, 'comments':None}
    except Exception as e:
        # print(f"[db.py(save_message_to_db)][Error]: {e}")
        return {'status':False,'comments':'Failed to save to db'}


def get_all_chat_session_ids()->list:
    try:
        with sl() as session:
            chat_sessions = session.scalars(select(ChatSessions.session_id)).fetchall()
        return chat_sessions
    except Exception as e:
        print(f"[db.py(get_all_chat_session_ids)][Error]: {e}")
        return []

def get_session_chats(session_id:str):
    try:
        with sl() as session:
            chats = session.scalars(select(ChatMessages).where(ChatMessages.chat_session_id == session_id).order_by(ChatMessages.sent_on)).fetchall()
            formated_chats = format_chats(chats)
        return formated_chats
    except Exception as e:
        print(f"[db.py(get_session_chats)][Error]: {e}")


def save_embeddings(vectors:list,document_id:int,chunks:list):
    try:
        with sl() as session:
            index = 1
            for embedding,chunk in zip(vectors,chunks):
                session.add(DocumentChunks(
                    document_id = document_id,
                    chunk_index = index,
                    chunk_text = chunk,
                    embeddings = embedding
                ))
                index += 1
            session.commit()
        return {'status': True,'comments':"No comments"}
    except Exception as e:
        print(f"[Error][curd.py(save_embeddings)]: {e}")
        return {'status':False, 'comments': f"failed to save embeddings {e}"}
    
def search_relavent_chunks(query_vector:list[float],session_id:int,limit:int = 5):
    with sl() as session:
        distance = DocumentChunks.embeddings.cosine_distance(query_vector)

        stmt = (
            select(DocumentChunks.chunk_text)
            .join(Documents, DocumentChunks.document_id == Documents.id)
            .where(Documents.session_id == session_id)
            .order_by(distance)
            .limit(limit)
        )
        result = session.execute(stmt).all()
        chunks = [chunk[0] for chunk in result]
        return chunks
            