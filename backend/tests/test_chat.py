"""Tests for chat endpoints."""

import uuid
from unittest.mock import patch, AsyncMock, MagicMock

import pytest


@pytest.mark.asyncio
class TestChatSessionCreate:
    """Tests for POST /api/v1/chat/sessions."""

    async def test_create_session(self, client, auth_headers, test_document):
        """Test creating a new chat session."""
        response = await client.post(
            "/api/v1/chat/sessions",
            json={
                "document_id": str(test_document.id),
                "title": "My Test Chat",
            },
            headers=auth_headers,
        )
        assert response.status_code == 201
        data = response.json()
        assert data["title"] == "My Test Chat"
        assert data["document_id"] == str(test_document.id)

    async def test_create_session_default_title(self, client, auth_headers, test_document):
        """Test creating a session with default title."""
        response = await client.post(
            "/api/v1/chat/sessions",
            json={"document_id": str(test_document.id)},
            headers=auth_headers,
        )
        assert response.status_code == 201
        assert response.json()["title"] == "New Chat"

    async def test_create_session_nonexistent_document(self, client, auth_headers):
        """Test creating a session for non-existent document."""
        response = await client.post(
            "/api/v1/chat/sessions",
            json={"document_id": str(uuid.uuid4())},
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_create_session_unauthenticated(self, client, test_document):
        """Test creating a session without authentication."""
        response = await client.post(
            "/api/v1/chat/sessions",
            json={"document_id": str(test_document.id)},
        )
        assert response.status_code == 403


@pytest.mark.asyncio
class TestChatSessionList:
    """Tests for GET /api/v1/chat/sessions."""

    async def test_list_sessions(self, client, auth_headers, test_chat_session):
        """Test listing chat sessions."""
        response = await client.get("/api/v1/chat/sessions", headers=auth_headers)
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1
        assert len(data["sessions"]) >= 1

    async def test_list_sessions_by_document(
        self, client, auth_headers, test_chat_session, test_document
    ):
        """Test listing sessions filtered by document."""
        response = await client.get(
            f"/api/v1/chat/sessions?document_id={test_document.id}",
            headers=auth_headers,
        )
        assert response.status_code == 200
        data = response.json()
        assert data["total"] >= 1


@pytest.mark.asyncio
class TestChatMessages:
    """Tests for message endpoints."""

    async def test_get_messages_empty(self, client, auth_headers, test_chat_session):
        """Test getting messages from empty session."""
        response = await client.get(
            f"/api/v1/chat/sessions/{test_chat_session.id}/messages",
            headers=auth_headers,
        )
        assert response.status_code == 200
        assert response.json() == []

    async def test_get_messages_nonexistent_session(self, client, auth_headers):
        """Test getting messages from non-existent session."""
        response = await client.get(
            f"/api/v1/chat/sessions/{uuid.uuid4()}/messages",
            headers=auth_headers,
        )
        assert response.status_code == 404

    async def test_send_message_streaming(self, client, auth_headers, test_chat_session):
        """Test sending a message returns streaming response."""
        async def mock_stream(*args, **kwargs):
            yield "Hello, "
            yield "this is a test response."

        with patch("app.routers.chat.vector_service") as mock_vs, \
             patch("app.routers.chat.gemini_service") as mock_gs:
            mock_vs.search.return_value = [
                {"text": "test context", "score": 0.9, "doc_id": "test"}
            ]
            mock_gs.chat_stream = mock_stream

            # Need to patch async_session_factory for the save operation
            with patch("app.routers.chat.async_session_factory") as mock_sf:
                mock_session = AsyncMock()
                mock_sf.return_value.__aenter__ = AsyncMock(return_value=mock_session)
                mock_sf.return_value.__aexit__ = AsyncMock(return_value=False)

                response = await client.post(
                    f"/api/v1/chat/sessions/{test_chat_session.id}/messages",
                    json={"content": "What is this document about?"},
                    headers=auth_headers,
                )

        assert response.status_code == 200
        assert "text/event-stream" in response.headers.get("content-type", "")

    async def test_send_message_nonexistent_session(self, client, auth_headers):
        """Test sending message to non-existent session."""
        response = await client.post(
            f"/api/v1/chat/sessions/{uuid.uuid4()}/messages",
            json={"content": "Hello?"},
            headers=auth_headers,
        )
        assert response.status_code == 404


@pytest.mark.asyncio
class TestChatSessionDelete:
    """Tests for DELETE /api/v1/chat/sessions/{id}."""

    async def test_delete_session(self, client, auth_headers, test_chat_session):
        """Test deleting a chat session."""
        response = await client.delete(
            f"/api/v1/chat/sessions/{test_chat_session.id}",
            headers=auth_headers,
        )
        assert response.status_code == 204

    async def test_delete_nonexistent_session(self, client, auth_headers):
        """Test deleting a non-existent session."""
        response = await client.delete(
            f"/api/v1/chat/sessions/{uuid.uuid4()}",
            headers=auth_headers,
        )
        assert response.status_code == 404
