"""Document Pydantic schemas."""

import uuid
from datetime import datetime

from pydantic import BaseModel


class DocumentResponse(BaseModel):
    """Schema for document response."""
    id: uuid.UUID
    user_id: uuid.UUID
    filename: str
    original_filename: str
    file_type: str
    file_size: int
    mime_type: str
    status: str
    transcript_text: str | None = None
    summary_text: str | None = None
    page_count: int | None = None
    duration_seconds: float | None = None
    highlights_json: str | None = None
    error_message: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class DocumentListResponse(BaseModel):
    """Schema for listing documents."""
    documents: list[DocumentResponse]
    total: int


class SummaryResponse(BaseModel):
    """Schema for document summary."""
    document_id: uuid.UUID
    summary: str


class HighlightItem(BaseModel):
    """Single highlight moment."""
    timestamp: float
    timestamp_formatted: str
    summary: str
    importance_score: float | None = None


class HighlightResponse(BaseModel):
    """Schema for Smart Highlight Reel."""
    document_id: uuid.UUID
    highlights: list[HighlightItem]
