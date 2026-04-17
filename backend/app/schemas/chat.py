"""Chat Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ChatSessionCreate(BaseModel):
    """Schema for creating a chat session."""
    document_id: uuid.UUID
    title: str = Field(default="New Chat", max_length=500)


class ChatSessionResponse(BaseModel):
    """Schema for chat session response."""
    id: uuid.UUID
    user_id: uuid.UUID
    document_id: uuid.UUID
    title: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageCreate(BaseModel):
    """Schema for sending a message."""
    content: str = Field(min_length=1, max_length=10000)


class TimestampReference(BaseModel):
    """A timestamp reference in an AI response."""
    time_seconds: float
    time_formatted: str
    label: str


class MessageResponse(BaseModel):
    """Schema for message response."""
    id: uuid.UUID
    session_id: uuid.UUID
    role: str
    content: str
    timestamps_json: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class ChatSessionListResponse(BaseModel):
    """Schema for listing chat sessions."""
    sessions: list[ChatSessionResponse]
    total: int
