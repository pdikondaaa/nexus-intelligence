# app/schemas/chat.py

from pydantic import BaseModel

class ChatRequest(BaseModel):
    query: str
    session_id: str