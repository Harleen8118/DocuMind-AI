"""File handling utilities."""

import os
import uuid
from pathlib import Path

from fastapi import HTTPException, UploadFile, status

from app.config import settings

ALLOWED_MIME_TYPES = {
    # PDF
    "application/pdf": "pdf",
    # Audio
    "audio/mpeg": "audio",
    "audio/mp3": "audio",
    "audio/wav": "audio",
    "audio/x-wav": "audio",
    "audio/ogg": "audio",
    "audio/flac": "audio",
    "audio/m4a": "audio",
    "audio/x-m4a": "audio",
    "audio/mp4": "audio",
    # Video
    "video/mp4": "video",
    "video/mpeg": "video",
    "video/webm": "video",
    "video/x-msvideo": "video",
    "video/quicktime": "video",
    "video/x-matroska": "video",
}

EXTENSION_TO_MIME = {
    ".pdf": "application/pdf",
    ".mp3": "audio/mpeg",
    ".wav": "audio/wav",
    ".ogg": "audio/ogg",
    ".flac": "audio/flac",
    ".m4a": "audio/m4a",
    ".mp4": "video/mp4",
    ".mpeg": "video/mpeg",
    ".webm": "video/webm",
    ".avi": "video/x-msvideo",
    ".mov": "video/quicktime",
    ".mkv": "video/x-matroska",
}


def get_upload_dir() -> Path:
    """Get and ensure the upload directory exists."""
    upload_dir = Path(settings.UPLOAD_DIR)
    upload_dir.mkdir(parents=True, exist_ok=True)
    return upload_dir


def generate_safe_filename(original_filename: str) -> str:
    """Generate a unique safe filename preserving extension."""
    ext = Path(original_filename).suffix.lower()
    unique_name = f"{uuid.uuid4().hex}{ext}"
    return unique_name


def validate_mime_type(content_type: str | None, filename: str) -> tuple[str, str]:
    """
    Validate the MIME type and return (mime_type, file_type).
    Falls back to extension-based detection if content_type is ambiguous.
    """
    ext = Path(filename).suffix.lower()

    # Try content_type first
    if content_type and content_type in ALLOWED_MIME_TYPES:
        return content_type, ALLOWED_MIME_TYPES[content_type]

    # Fall back to extension
    if ext in EXTENSION_TO_MIME:
        mime = EXTENSION_TO_MIME[ext]
        return mime, ALLOWED_MIME_TYPES[mime]

    raise HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=f"Unsupported file type: {content_type or ext}. "
               f"Supported: PDF, audio (mp3, wav, ogg, flac, m4a), "
               f"video (mp4, webm, avi, mov, mkv)",
    )


def validate_file_size(file_size: int) -> None:
    """Validate file size against configured maximum."""
    max_bytes = settings.MAX_FILE_SIZE_MB * 1024 * 1024
    if file_size > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size ({file_size / 1024 / 1024:.1f}MB) exceeds "
                   f"maximum allowed size ({settings.MAX_FILE_SIZE_MB}MB)",
        )


async def save_upload_file(upload_file: UploadFile) -> tuple[str, int]:
    """
    Save an uploaded file to the upload directory.
    Returns (saved_filename, file_size).
    """
    upload_dir = get_upload_dir()
    safe_name = generate_safe_filename(upload_file.filename or "unknown")
    file_path = upload_dir / safe_name

    file_size = 0
    chunk_size = 1024 * 1024  # 1MB chunks

    with open(file_path, "wb") as f:
        while True:
            chunk = await upload_file.read(chunk_size)
            if not chunk:
                break
            file_size += len(chunk)
            # Check size during upload to fail fast
            validate_file_size(file_size)
            f.write(chunk)

    return safe_name, file_size


def delete_file(filename: str) -> None:
    """Delete a file from the upload directory."""
    file_path = get_upload_dir() / filename
    if file_path.exists():
        os.remove(file_path)


def get_file_path(filename: str) -> Path:
    """Get the full path to an uploaded file."""
    return get_upload_dir() / filename
