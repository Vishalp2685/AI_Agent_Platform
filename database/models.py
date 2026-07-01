from .database import Base
from sqlalchemy import ForeignKey
from pgvector.sqlalchemy import Vector
from sqlalchemy.orm import Mapped, mapped_column
from schemas import Role,Models
from datetime import datetime,timezone

class ChatMessages(Base):
    __tablename__ = 'chatmessages'

    id:Mapped[int] = mapped_column(autoincrement=True,nullable=False,primary_key=True)
    chat_session_id:Mapped[str] = mapped_column(nullable=False)
    message:Mapped[str] = mapped_column(nullable=False)
    role: Mapped[Role] = mapped_column(nullable=False)
    model_used: Mapped[Models] = mapped_column(nullable=False)
    sent_on: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))

class ChatSessions(Base):
    __tablename__ = 'chat_sessions'

    session_id: Mapped[str] = mapped_column(primary_key=True)

class Documents(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey(ChatSessions.session_id),nullable=False)
    file_name: Mapped[str] = mapped_column(nullable=False)
    file_at: Mapped[str] = mapped_column(nullable=False)
    uploaded_at: Mapped[datetime] = mapped_column(default=lambda:datetime.now(timezone.utc))

class DocumentChunks(Base):
    __tablename__ = 'document_chunks'

    id: Mapped[int] = mapped_column(primary_key=True,autoincrement=True)
    document_id:Mapped[int] = mapped_column(ForeignKey(Documents.id))
    chunk_index: Mapped[int] 
    chunk_text: Mapped[str]
    embeddings: Mapped[float] = mapped_column(Vector(384))