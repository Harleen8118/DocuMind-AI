"""Document management router: upload, list, delete, summarize, highlights."""

import json
import logging
import uuid

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, UploadFile, File, status
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db, async_session_factory
from app.models.document import Document, FileType, ProcessingStatus
from app.models.user import User
from app.schemas.document import (
    DocumentResponse,
    DocumentListResponse,
    SummaryResponse,
    HighlightResponse,
    HighlightItem,
)
from app.services.gemini_service import gemini_service
from app.services.highlight_service import highlight_service
from app.services.pdf_service import pdf_service
from app.services.vector_service import vector_service
from app.services.whisper_service import whisper_service
from app.utils.auth import get_current_user
from app.utils.file_utils import (
    delete_file,
    get_file_path,
    save_upload_file,
    validate_mime_type,
)

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/documents", tags=["Documents"])


async def process_document(document_id: uuid.UUID):
    """Background task: process uploaded document (extract, transcribe, index)."""
    async with async_session_factory() as db:
        try:
            result = await db.execute(
                select(Document).where(Document.id == document_id)
            )
            doc = result.scalar_one_or_none()
            if not doc:
                return

            doc.status = ProcessingStatus.PROCESSING
            await db.commit()

            file_path = get_file_path(doc.filename)
            doc_id_str = str(doc.id)

            if doc.file_type == FileType.PDF:
                # Extract text from PDF
                pages = pdf_service.extract_text(file_path)
                doc.page_count = pdf_service.get_page_count(file_path)
                full_text = pdf_service.get_full_text(pages)
                doc.transcript_text = full_text

                # Extract images
                pdf_service.extract_images(file_path, doc_id_str)

                # Index in FAISS
                page_numbers = [p["page_number"] for p in pages]
                vector_service.add_document(
                    doc_id=doc_id_str,
                    text=full_text,
                    page_numbers=page_numbers,
                )

            elif doc.file_type in (FileType.AUDIO, FileType.VIDEO):
                # Transcribe audio/video
                transcript_data = whisper_service.transcribe(
                    file_path=file_path,
                    file_type=doc.file_type.value,
                )
                doc.transcript_text = transcript_data["text"]
                doc.duration_seconds = transcript_data["duration"]

                # Index in FAISS using segments
                vector_service.add_document(
                    doc_id=doc_id_str,
                    text=transcript_data["text"],
                    segments=transcript_data["segments"],
                )

                # Generate Smart Highlight Reel for video
                if doc.file_type == FileType.VIDEO and transcript_data["segments"]:
                    try:
                        highlights = await highlight_service.generate_highlights(
                            transcript_text=transcript_data["text"],
                            segments=transcript_data["segments"],
                            duration=transcript_data["duration"],
                        )
                        doc.highlights_json = highlight_service.highlights_to_json(
                            highlights
                        )
                    except Exception as e:
                        logger.error(f"Highlight generation failed: {e}")

            doc.status = ProcessingStatus.READY
            await db.commit()
            logger.info(f"Document {document_id} processed successfully")

        except Exception as e:
            logger.error(f"Error processing document {document_id}: {e}")
            try:
                doc.status = ProcessingStatus.ERROR
                doc.error_message = str(e)
                await db.commit()
            except Exception:
                pass


@router.post(
    "/upload",
    response_model=DocumentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload a document",
)
async def upload_document(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Upload a PDF, audio, or video file for processing."""
    # Validate file type
    mime_type, file_type = validate_mime_type(file.content_type, file.filename or "")

    # Save file
    safe_filename, file_size = await save_upload_file(file)

    # Create document record
    document = Document(
        user_id=current_user.id,
        filename=safe_filename,
        original_filename=file.filename or "unknown",
        file_type=FileType(file_type),
        file_size=file_size,
        mime_type=mime_type,
        status=ProcessingStatus.PENDING,
    )
    db.add(document)
    await db.flush()
    await db.refresh(document)

    # Start background processing
    background_tasks.add_task(process_document, document.id)

    return DocumentResponse.model_validate(document)


@router.get(
    "/",
    response_model=DocumentListResponse,
    summary="List user documents",
)
async def list_documents(
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List all documents for the current user."""
    # Get total count
    count_result = await db.execute(
        select(func.count(Document.id)).where(Document.user_id == current_user.id)
    )
    total = count_result.scalar() or 0

    # Get documents
    result = await db.execute(
        select(Document)
        .where(Document.user_id == current_user.id)
        .order_by(Document.created_at.desc())
        .offset(skip)
        .limit(limit)
    )
    documents = result.scalars().all()

    return DocumentListResponse(
        documents=[DocumentResponse.model_validate(d) for d in documents],
        total=total,
    )


@router.get(
    "/{document_id}",
    response_model=DocumentResponse,
    summary="Get document details",
)
async def get_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get details of a specific document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    return DocumentResponse.model_validate(document)


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a document",
)
async def delete_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a document and its associated file."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    # Remove from FAISS
    vector_service.remove_document(str(document.id))

    # Delete file
    delete_file(document.filename)

    # Delete from DB
    await db.delete(document)


@router.post(
    "/{document_id}/summarize",
    response_model=SummaryResponse,
    summary="Generate document summary",
)
async def summarize_document(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Generate an AI summary of the document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.status != ProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Document is not ready (status: {document.status.value})",
        )

    if not document.transcript_text:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No text content available for summarization",
        )

    # Check cache
    if document.summary_text:
        return SummaryResponse(
            document_id=document.id, summary=document.summary_text
        )

    # Generate summary
    summary = await gemini_service.summarize_document(
        text=document.transcript_text,
        document_type=document.file_type.value,
    )

    # Cache in DB
    document.summary_text = summary
    await db.commit()

    return SummaryResponse(document_id=document.id, summary=summary)


@router.get(
    "/{document_id}/highlights",
    response_model=HighlightResponse,
    summary="Get Smart Highlight Reel",
)
async def get_highlights(
    document_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get the Smart Highlight Reel for a video document."""
    result = await db.execute(
        select(Document).where(
            Document.id == document_id, Document.user_id == current_user.id
        )
    )
    document = result.scalar_one_or_none()

    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Document not found"
        )

    if document.file_type not in (FileType.VIDEO, FileType.AUDIO):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Highlights are only available for video and audio files",
        )

    if document.status != ProcessingStatus.READY:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Document is still being processed",
        )

    highlights_data = highlight_service.highlights_from_json(document.highlights_json)

    if not highlights_data and document.transcript_text:
        # Generate on demand if not yet generated
        try:
            segments_data = json.loads(document.transcript_text) if document.transcript_text.startswith("[") else []
        except json.JSONDecodeError:
            segments_data = []

        # If we don't have segments, create simple ones from text
        if not segments_data:
            search_results = vector_service.search(
                query="important key moments summary",
                doc_id=str(document.id),
                top_k=20,
            )
            segments_data = [
                {
                    "text": r["text"],
                    "start": r.get("start_time", 0),
                    "end": r.get("end_time", 0),
                }
                for r in search_results
            ]

        if segments_data:
            highlights_data = await highlight_service.generate_highlights(
                transcript_text=document.transcript_text,
                segments=segments_data,
                duration=document.duration_seconds or 0,
            )
            document.highlights_json = highlight_service.highlights_to_json(highlights_data)
            await db.commit()

    highlights = [
        HighlightItem(
            timestamp=h["timestamp"],
            timestamp_formatted=h["timestamp_formatted"],
            summary=h["summary"],
            importance_score=h.get("importance_score"),
        )
        for h in highlights_data
    ]

    return HighlightResponse(document_id=document.id, highlights=highlights)
