"""Tests for Smart Highlight Reel service."""

import json
from unittest.mock import patch, AsyncMock

import pytest

from app.services.highlight_service import HighlightService


@pytest.mark.asyncio
class TestHighlightService:
    """Tests for HighlightService."""

    def setup_method(self):
        """Create a fresh service instance."""
        self.service = HighlightService()

    async def test_generate_highlights(self):
        """Test generating highlights from transcript."""
        mock_highlights = [
            {"timestamp": 15.0, "timestamp_formatted": "00:15", "summary": "Introduction", "importance_score": 0.8},
            {"timestamp": 60.0, "timestamp_formatted": "01:00", "summary": "Key insight", "importance_score": 0.95},
            {"timestamp": 120.0, "timestamp_formatted": "02:00", "summary": "Conclusion", "importance_score": 0.7},
        ]

        with patch("app.services.highlight_service.gemini_service") as mock_gemini:
            mock_gemini.generate_highlights = AsyncMock(return_value=mock_highlights)

            result = await self.service.generate_highlights(
                transcript_text="Full transcript text...",
                segments=[
                    {"text": "Intro", "start": 0, "end": 30},
                    {"text": "Key insight", "start": 45, "end": 90},
                    {"text": "Conclusion", "start": 100, "end": 150},
                ],
                duration=150.0,
            )

        assert len(result) == 3
        assert result[0]["timestamp"] == 15.0
        assert result[1]["importance_score"] == 0.95

    async def test_generate_highlights_empty_segments(self):
        """Test with empty segments returns empty list."""
        result = await self.service.generate_highlights(
            transcript_text="",
            segments=[],
        )
        assert result == []

    async def test_generate_highlights_filters_invalid_timestamps(self):
        """Test that highlights with invalid timestamps are filtered."""
        mock_highlights = [
            {"timestamp": 10.0, "timestamp_formatted": "00:10", "summary": "Valid", "importance_score": 0.9},
            {"timestamp": 200.0, "timestamp_formatted": "03:20", "summary": "Beyond duration", "importance_score": 0.8},
        ]

        with patch("app.services.highlight_service.gemini_service") as mock_gemini:
            mock_gemini.generate_highlights = AsyncMock(return_value=mock_highlights)

            result = await self.service.generate_highlights(
                transcript_text="Short video",
                segments=[{"text": "Content", "start": 0, "end": 60}],
                duration=60.0,
            )

        assert len(result) == 1
        assert result[0]["timestamp"] == 10.0

    async def test_generate_highlights_limits_to_five(self):
        """Test that at most 5 highlights are returned."""
        mock_highlights = [
            {"timestamp": i * 10.0, "timestamp_formatted": f"00:{i*10:02d}", "summary": f"Moment {i}", "importance_score": 0.5 + i * 0.05}
            for i in range(8)
        ]

        with patch("app.services.highlight_service.gemini_service") as mock_gemini:
            mock_gemini.generate_highlights = AsyncMock(return_value=mock_highlights)

            result = await self.service.generate_highlights(
                transcript_text="Long video",
                segments=[{"text": f"Segment {i}", "start": i * 10, "end": (i + 1) * 10} for i in range(8)],
                duration=300.0,
            )

        assert len(result) <= 5

    async def test_generate_highlights_error_handling(self):
        """Test that errors return empty list."""
        with patch("app.services.highlight_service.gemini_service") as mock_gemini:
            mock_gemini.generate_highlights = AsyncMock(side_effect=Exception("API Error"))

            result = await self.service.generate_highlights(
                transcript_text="Test",
                segments=[{"text": "Test", "start": 0, "end": 5}],
            )

        assert result == []

    def test_highlights_to_json(self):
        """Test serialization to JSON."""
        highlights = [
            {"timestamp": 10.0, "summary": "Test", "importance_score": 0.9},
        ]
        json_str = HighlightService.highlights_to_json(highlights)
        assert isinstance(json_str, str)
        parsed = json.loads(json_str)
        assert len(parsed) == 1

    def test_highlights_from_json(self):
        """Test deserialization from JSON."""
        json_str = json.dumps([
            {"timestamp": 10.0, "summary": "Test"},
        ])
        result = HighlightService.highlights_from_json(json_str)
        assert len(result) == 1
        assert result[0]["timestamp"] == 10.0

    def test_highlights_from_json_none(self):
        """Test deserialization from None returns empty list."""
        assert HighlightService.highlights_from_json(None) == []

    def test_highlights_from_json_invalid(self):
        """Test deserialization from invalid JSON returns empty list."""
        assert HighlightService.highlights_from_json("not json") == []
