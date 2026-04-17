"""Tests for document endpoints."""

import io
import uuid
from unittest.mock import patch, AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
class TestDocumentUpload:
    """Tests for POST /api/v1/documents/upload."""

    async def test_upload_pdf(self, client, auth_headers, upload_dir):
        """Test uploading a PDF file."""
        pdf_content = b"%PDF-1.4 test content"
        files = {"file": ("test.pdf", io.BytesIO(pdf_content), "application/pdf")}

        with patch("app.routers.documents.process_document", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["original_filename"] == "test.pdf"
        assert data["file_type"] == "pdf"
        assert data["status"] == "pending"

    async def test_upload_audio(self, client, auth_headers, upload_dir):
        """Test uploading an audio file."""
        audio_content = b"fake audio content"
        files = {"file": ("test.mp3", io.BytesIO(audio_content), "audio/mpeg")}

        with patch("app.routers.documents.process_document", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "audio"

    async def test_upload_video(self, client, auth_headers, upload_dir):
        """Test uploading a video file."""
        video_content = b"fake video content"
        files = {"file": ("test.mp4", io.BytesIO(video_content), "video/mp4")}

        with patch("app.routers.documents.process_document", new_callable=AsyncMock):
            response = await client.post(
                "/api/v1/documents/upload",
                files=files,
                headers=auth_headers,
            )

        assert response.status_code == 201
        data = response.json()
        assert data["file_type"] == "video"

    async def test_upload_unsupported_type(self, client, auth_headers, upload_dir):
        """Test uploading an unsupported file type."""
        files = {"file": ("test.exe", io.BytesIO(b"binary"), "application/x-msdownload")}

        response = await client.post(
            "/api/v1/documents/upload",
            files=files,
            headers=auth_headers,
        )

        assert response.status_code == 400

    async def test_upload_unauthenticated(self, client, upload_dir):
        """Test uploading without authentication."""
        files = {"file": ("test.pdf", io.BytesIO(b"content"), "application/pdf")}
        response = await client.post("/api/v1/documents/upload", files=files)
        assert response.status_code == 403


@pytest.mark.asyncio
class TestDocumentList:
    """Tests for GET /api/v1/documents/."""

    async def test_list_documents(self, client, auth_headers, test_document):
        """Test listing user documents."""
        response = await client.get("/api/v1/documents/", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["documents"]) >= 1
        assert data["documents"][0]["original_filename"] == "test_document.pdf"

    async def test_list_documents_empty(self, client):
        """Test listing documents for new user with no documents."""
        # Register a new user
        reg_response = await client.post(
            "/api/v1/auth/register",
            json={
                "email": "empty@example.com",
                "username": "emptyuser",
                "password": "securepassword123",
            },
        )
        token = reg_response.json()["access_token"]

        response = await client.get(
            "/api/v1/documents/",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] == 0
        assert data["documents"] == []


@pytest.mark.asyncio
class TestDocumentGet:
    """Tests for GET /api/v1/documents/{id}."""

    async def test_get_document(self, client, auth_headers, test_document):
        """Test getting a specific document."""
        response = await client.get(
            f"/api/v1/documents/{test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == str(test_document.id)

    async def test_get_nonexistent_document(self, client, auth_headers):
        """Test getting a non-existent document."""
        response = await client.get(
            f"/api/v1/documents/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDocumentDelete:
    """Tests for DELETE /api/v1/documents/{id}."""

    async def test_delete_document(self, client, auth_headers, test_document):
        """Test deleting a document."""
        with patch("app.routers.documents.vector_service") as mock_vs:
            mock_vs.remove_document.return_value = 0
            with patch("app.routers.documents.delete_file"):
                response = await client.delete(
                    f"/api/v1/documents/{test_document.id}",
                    headers=auth_headers,
                )

        assert response.status_code == 204

    async def test_delete_nonexistent_document(self, client, auth_headers):
        """Test deleting a non-existent document."""
        response = await client.delete(
            f"/api/v1/documents/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDocumentSummarize:
    """Tests for POST /api/v1/documents/{id}/summarize."""

    async def test_summarize_document(self, client, auth_headers, test_document):
        """Test generating a document summary."""
        with patch("app.routers.documents.gemini_service") as mock_gemini:
            mock_gemini.summarize_document = AsyncMock(
                return_value="This is a comprehensive summary of the document."
            )
            response = await client.post(
                f"/api/v1/documents/{test_document.id}/summarize",
                headers=auth_headers,
            )

        assert response.status_code == 200
        data = response.json()
        assert "summary" in data
        assert data["document_id"] == str(test_document.id)

    async def test_summarize_nonexistent_document(self, client, auth_headers):
        """Test summarizing a non-existent document."""
        response = await client.post(
            f"/api/v1/documents/{uuid.uuid4()}/summarize",
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestDocumentHighlights:
    """Tests for GET /api/v1/documents/{id}/highlights."""

    async def test_get_highlights(self, client, auth_headers, test_video_document):
        """Test getting highlights for a video document."""
        response = await client.get(
            f"/api/v1/documents/{test_video_document.id}/highlights",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert len(data["highlights"]) == 2
        assert data["highlights"][0]["timestamp"] == 10.0
        assert data["highlights"][0]["summary"] == "Introduction"

    async def test_highlights_pdf_document(self, client, auth_headers, test_document):
        """Test that highlights are rejected for PDF documents."""
        response = await client.get(
            f"/api/v1/documents/{test_document.id}/highlights",
            headers=auth_headers,
        )
        assert response.status_code == 400
