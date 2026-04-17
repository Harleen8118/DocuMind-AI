"""Tests for Gemini service."""

import json
from unittest.mock import patch, MagicMock, AsyncMock

import pytest

from app.services.gemini_service import GeminiService


@pytest.mark.asyncio
class TestGeminiService:
    """Tests for GeminiService."""

    def setup_method(self):
        """Create a fresh service instance for each test."""
        self.service = GeminiService()

    async def test_chat_with_context(self):
        """Test chat with document context."""
        mock_response = MagicMock()
        mock_response.text = "Based on the document, machine learning is discussed on page 2."

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            result = await self.service.chat_with_context(
                query="What is machine learning?",
                context_chunks=[
                    {"text": "Machine learning is a branch of AI.", "page_number": 2}
                ],
            )

        assert "machine learning" in result.lower()

    async def test_chat_with_timestamps(self):
        """Test chat response includes timestamps for audio/video."""
        mock_response = MagicMock()
        mock_response.text = (
            "At 02:30, the speaker discusses AI.\n"
            'TIMESTAMPS: [{"time_seconds": 150, "time_formatted": "02:30", "label": "AI discussion"}]'
        )

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = mock_response

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            result = await self.service.chat_with_context(
                query="When is AI discussed?",
                context_chunks=[
                    {"text": "Discussion about AI", "start_time": 150, "end_time": 180}
                ],
                document_type="video",
            )

        assert "TIMESTAMPS" in result

    async def test_summarize_document(self):
        """Test document summarization."""
        mock_response = MagicMock()
        mock_response.text = "**Main Topics**: AI and ML\n**Key Points**: - Neural networks are important"

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            result = await self.service.summarize_document(
                text="This document is about AI and machine learning...",
                document_type="pdf",
            )

        assert "AI" in result

    async def test_generate_highlights(self):
        """Test highlight generation returns valid format."""
        highlights_json = json.dumps([
            {"timestamp": 30.0, "summary": "Opening remarks", "importance_score": 0.8},
            {"timestamp": 120.5, "summary": "Key finding", "importance_score": 0.95},
        ])

        mock_response = MagicMock()
        mock_response.text = highlights_json

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            result = await self.service.generate_highlights(
                transcript_text="Opening remarks... Key finding about research...",
                segments=[
                    {"start": 0, "end": 60, "text": "Opening remarks"},
                    {"start": 60, "end": 180, "text": "Key finding about research"},
                ],
            )

        assert len(result) == 2
        assert result[0]["timestamp"] == 30.0
        assert result[0]["timestamp_formatted"] == "00:30"
        assert "summary" in result[0]

    async def test_generate_highlights_json_in_code_block(self):
        """Test parsing highlights from markdown code block response."""
        highlights_json = json.dumps([
            {"timestamp": 45.0, "summary": "Important moment", "importance_score": 0.9},
        ])
        response_text = f"```json\n{highlights_json}\n```"

        mock_response = MagicMock()
        mock_response.text = response_text

        mock_model = MagicMock()
        mock_model.generate_content.return_value = mock_response

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            result = await self.service.generate_highlights(
                transcript_text="Important moment at 45 seconds",
                segments=[{"start": 30, "end": 60, "text": "Important moment"}],
            )

        assert len(result) == 1

    async def test_format_time(self):
        """Test time formatting utility."""
        assert GeminiService._format_time(0) == "00:00"
        assert GeminiService._format_time(65) == "01:05"
        assert GeminiService._format_time(3661) == "01:01:01"
        assert GeminiService._format_time(30.7) == "00:30"

    async def test_chat_stream(self):
        """Test streaming chat response."""
        mock_chunk1 = MagicMock()
        mock_chunk1.text = "Hello, "
        mock_chunk2 = MagicMock()
        mock_chunk2.text = "world!"

        mock_chat = MagicMock()
        mock_chat.send_message.return_value = [mock_chunk1, mock_chunk2]

        mock_model = MagicMock()
        mock_model.start_chat.return_value = mock_chat

        with patch("app.services.gemini_service.genai") as mock_genai:
            mock_genai.GenerativeModel.return_value = mock_model
            mock_genai.types.GenerationConfig.return_value = {}

            chunks = []
            async for chunk in self.service.chat_stream(
                query="Hello",
                context_chunks=[{"text": "test context"}],
            ):
                chunks.append(chunk)

        assert len(chunks) > 0
