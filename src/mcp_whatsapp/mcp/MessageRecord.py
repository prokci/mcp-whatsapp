from sqlalchemy import Boolean, Column, DateTime, Integer, String, Text

from src.mcp_whatsapp.data_base.DBContext import SQLModel


class MessageRecord(SQLModel):
    __tablename__ = "whatsapp_messages"

    id = Column(Integer, primary_key=True, autoincrement=True)
    message_id = Column(String, index=True)
    pushname = Column(String, nullable=True)
    sender = Column(String, nullable=True)
    is_from_me = Column(Boolean, default=False)
    text = Column(Text, nullable=True)
    chat_user = Column(String, nullable=True)
    file_path = Column(String, nullable=True)
    version = Column(Integer, default=1)
    datetime = Column(DateTime(timezone=True), nullable=True)
