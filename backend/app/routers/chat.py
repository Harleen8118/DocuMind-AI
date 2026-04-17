"""Chat router: sessions, messages, streaming responses."""

import json
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database import get_db, async_session_factory
from app.models.chat import ChatSession, Message, MessageRole
from app.models.document import Document, ProcessingStatus
from app.models.user import User
from app.schemas.chat import (
    ChatSessionCreate,
    ChatSessionResponse,
    ChatSessionListResponse,
    MessageCreate,
    MessageResponse,
)
from app.services.gemini_service import gemini_service
from app.services.vector_service import vector_service
from app.utils.auth import get_current_user

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post(
    "/sessions",
    response_model=ChatSessionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a chat session",
)
async def create_session(
    session_data: ChatSessionCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Create a new chat session linked to a document."""
    # Verify document exists and belongs to user
    result = await db.execute(
        select(Document).where(
            Document.id == session_data.document_id,
            Document.user_id == current_user.id,
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
            detail="Document is still being processed",
        )

    session = ChatSession(
        user_id=current_user.id,
        document_id=session_data.document_id,
        title=session_data.title,
    )
    db.add(session)
    await db.flush()
    await db.refresh(session)

    return ChatSessionResponse.model_validate(session)


@router.get(
    "/sessions",
    response_model=ChatSessionListResponse,
    summary="List chat sessions",
)
async def list_sessions(
    document_id: uuid.UUID | None = None,
    skip: int = 0,
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """List chat sessions for the current user, optionally filtered by document."""
    query = select(ChatSession).where(ChatSession.user_id == current_user.id)
    count_query = select(func.count(ChatSession.id)).where(
        ChatSession.user_id == current_user.id
    )

    if document_id:
        query = query.where(ChatSession.document_id == document_id)
        count_query = count_query.where(ChatSession.document_id == document_id)

    count_result = await db.execute(count_query)
    total = count_result.scalar() or 0

    result = await db.execute(
        query.order_by(ChatSession.created_at.desc()).offset(skip).limit(limit)
    )
    sessions = result.scalars().all()

    return ChatSessionListResponse(
        sessions=[ChatSessionResponse.model_validate(s) for s in sessions],
        total=total,
    )


@router.get(
    "/sessions/{session_id}/messages",
    response_model=list[MessageResponse],
    summary="Get message history",
)
async def get_messages(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Get all messages in a chat session."""
    # Verify session belongs to user
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
        )

    # Get messages
    result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.asc())
    )
    messages = result.scalars().all()

    return [MessageResponse.model_validate(m) for m in messages]


@router.post(
    "/sessions/{session_id}/messages",
    summary="Send a message (streaming)",
)
async def send_message(
    session_id: uuid.UUID,
    message_data: MessageCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Send a message and get a streaming AI response via Server-Sent Events.

    The response uses SSE format:
    - data: {chunk} — for each text chunk
    - data: [TIMESTAMPS]{json} — for timestamp references
    - data: [DONE] — when response is complete
    """
    # Verify session
    result = await db.execute(
        select(ChatSession)
        .where(ChatSession.id == session_id, ChatSession.user_id == current_user.id)
        .options(selectinload(ChatSession.document))
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
        )

    document = session.document
    if not document:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Associated document not found"
        )

    # Save user message
    user_message = Message(
        session_id=session_id,
        role=MessageRole.USER,
        content=message_data.content,
    )
    db.add(user_message)
    await db.flush()

    # Get context from semantic search
    context_chunks = vector_service.search(
        query=message_data.content,
        doc_id=str(document.id),
        top_k=5,
    )

    # Get chat history
    history_result = await db.execute(
        select(Message)
        .where(Message.session_id == session_id)
        .order_by(Message.created_at.desc())
        .limit(20)
    )
    history_messages = list(reversed(history_result.scalars().all()))
    chat_history = [
        {"role": m.role.value, "content": m.content} for m in history_messages
    ]

    # Stream response
    async def generate_stream():
        full_response = ""
        timestamps_json = None

        try:
            async for chunk in gemini_service.chat_stream(
                query=message_data.content,
                context_chunks=context_chunks,
                chat_history=chat_history,
                document_type=document.file_type.value,
            ):
                full_response += chunk

                # Check if this chunk contains timestamps
                if "TIMESTAMPS:" in chunk:
                    parts = chunk.split("TIMESTAMPS:")
                    text_part = parts[0]
                    if text_part:
                        yield f"data: {text_part}\n\n"
                    if len(parts) > 1:
                        timestamps_str = parts[1].strip()
                        yield f"data: [TIMESTAMPS]{timestamps_str}\n\n"
                        timestamps_json = timestamps_str
                else:
                    yield f"data: {chunk}\n\n"

            # Save assistant message
            # Extract clean text (without TIMESTAMPS marker)
            clean_response = full_response
            if "TIMESTAMPS:" in clean_response:
                clean_response = clean_response.split("TIMESTAMPS:")[0].strip()

            async with async_session_factory() as save_db:
                assistant_message = Message(
                    session_id=session_id,
                    role=MessageRole.ASSISTANT,
                    content=clean_response,
                    timestamps_json=timestamps_json,
                )
                save_db.add(assistant_message)
                await save_db.commit()

        except Exception as e:
            logger.error(f"Streaming error: {e}")
            yield f"data: [ERROR]{str(e)}\n\n"

        yield "data: [DONE]\n\n"

    return StreamingResponse(
        generate_stream(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


@router.delete(
    "/sessions/{session_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a chat session",
)
async def delete_session(
    session_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """Delete a chat session and all its messages."""
    result = await db.execute(
        select(ChatSession).where(
            ChatSession.id == session_id, ChatSession.user_id == current_user.id
        )
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="Chat session not found"
        )

    await db.delete(session)
