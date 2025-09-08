from datetime import datetime
from typing import Optional, Dict, Any, List
from sqlmodel import SQLModel, Field
from sqlalchemy import Column, String, Text
import json
from pydantic import BaseModel


class BotBase(SQLModel):
    name: str
    description: Optional[str] = None
    owner: str = "default"


class Bot(BotBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    slug: str = Field(unique=True, index=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)


class BotCreate(BotBase):
    pass


class BotRead(BotBase):
    id: int
    slug: str
    created_at: datetime


class DocumentBase(SQLModel):
    filename: str
    filetype: str
    pages: Optional[int] = None
    status: str = "PENDING"  # PENDING, PARSING, CHUNKING, EMBEDDING, INDEXING, DONE, ERROR
    doc_metadata: str = Field(default="{}", sa_column=Column(Text, nullable=True))


class Document(DocumentBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: int = Field(foreign_key="bot.id")
    path_original: str
    path_parsed: Optional[str] = None
    created_at: datetime = Field(default_factory=datetime.utcnow)


class DocumentCreate(DocumentBase):
    bot_id: int


class DocumentRead(DocumentBase):
    id: int
    bot_id: int
    path_original: str
    path_parsed: Optional[str]
    created_at: datetime


class ChunkBase(SQLModel):
    chunk_id: str
    text: str
    location: str = Field(default="{}", sa_column=Column(Text, nullable=True))  # page, paragraph, cell
    headings: str = Field(default="[]", sa_column=Column(Text, nullable=True))


class Chunk(ChunkBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: int = Field(foreign_key="bot.id")
    document_id: int = Field(foreign_key="document.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChunkCreate(ChunkBase):
    bot_id: int
    document_id: int


class ChunkRead(ChunkBase):
    id: int
    bot_id: int
    document_id: int
    created_at: datetime


class ChatBase(SQLModel):
    pass


class Chat(ChatBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: int = Field(foreign_key="bot.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ChatCreate(ChatBase):
    bot_id: int


class ChatRead(ChatBase):
    id: int
    bot_id: int
    created_at: datetime


class MessageBase(SQLModel):
    role: str  # user, assistant
    content: str
    sources: str = Field(default="[]", sa_column=Column(Text, nullable=True))


class Message(MessageBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    chat_id: int = Field(foreign_key="chat.id")
    created_at: datetime = Field(default_factory=datetime.utcnow)


class MessageCreate(MessageBase):
    chat_id: int


class MessageRead(MessageBase):
    id: int
    chat_id: int
    created_at: datetime


class UrlSourceBase(SQLModel):
    root_url: str
    depth: int = 1
    status: str = "PENDING"  # PENDING, CRAWLING, DONE, ERROR


class UrlSource(UrlSourceBase, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    bot_id: int = Field(foreign_key="bot.id")
    fetched_urls: str = Field(default="[]", sa_column=Column(Text, nullable=True))
    created_at: datetime = Field(default_factory=datetime.utcnow)


class UrlSourceCreate(UrlSourceBase):
    bot_id: int


class UrlSourceRead(UrlSourceBase):
    id: int
    bot_id: int
    fetched_urls: List[str]
    created_at: datetime


# Pydantic models for API requests/responses
class ChatRequest(BaseModel):
    message: str
    chat_id: Optional[int] = None


class ChatResponse(BaseModel):
    message: str
    sources: List[Dict[str, Any]]
    chat_id: int


class UploadResponse(BaseModel):
    task_id: str
    message: str


class TaskBase(SQLModel):
    type: str
    data: str = Field(default="{}", sa_column=Column(Text, nullable=True))
    status: str = "PENDING"
    result: Optional[str] = Field(default=None, sa_column=Column(Text, nullable=True))
    error: Optional[str] = None


class Task(TaskBase, table=True):
    id: str = Field(primary_key=True)
    created_at: datetime = Field(default_factory=datetime.utcnow)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None


class TaskCreate(TaskBase):
    pass


class TaskRead(TaskBase):
    id: str
    created_at: datetime
    started_at: Optional[datetime]
    completed_at: Optional[datetime]


class StatusResponse(BaseModel):
    status: str
    progress: Optional[float] = None
    message: Optional[str] = None
