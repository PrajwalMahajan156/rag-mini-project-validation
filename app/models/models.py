from sqlalchemy import Column, Integer, String, ForeignKey, Text, DateTime
from sqlalchemy.orm import relationship
from app.core.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)

    documents = relationship("Document", back_populates="owner")
    chat_messages = relationship("ChatMessage", back_populates="user")

class Document(Base):
    __tablename__ = "documents"

    id = Column(String, primary_key=True, index=True) # Using UUID from logic
    filename = Column(String)
    user_id = Column(Integer, ForeignKey("users.id"))

    owner = relationship("User", back_populates="documents")
    chat_messages = relationship("ChatMessage", back_populates="document")

class ChatMessage(Base):
    __tablename__ = "chat_messages"

    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String, index=True)
    role = Column(String) # 'user' or 'bot'
    content = Column(Text)
    timestamp = Column(DateTime, default=datetime.utcnow)
    user_id = Column(Integer, ForeignKey("users.id"))
    document_id = Column(String, ForeignKey("documents.id"))

    input_tokens = Column(Integer, nullable=True)
    output_tokens = Column(Integer, nullable=True)

    user = relationship("User", back_populates="chat_messages")
    document = relationship("Document", back_populates="chat_messages")
