"""Tests for Whisper transcription service."""

from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.services.whisper_service import WhisperService


@pytest.mark.asyncio
class TestWhisperService:
    """Tests for WhisperService."""

    def setup_method(self):
        """Create a fresh service instance for each test."""
        self.service = WhisperService()

    def test_format_timestamp(self):
        """Test timestamp formatting."""
        assert WhisperService.format_timestamp(0) == "00:00"
        assert WhisperService.format_timestamp(30) == "00:30"
        assert WhisperService.format_timestamp(65) == "01:05"
        assert WhisperService.format_timestamp(3661) == "01:01:01"

    def test_transcribe_audio(self, tmp_path):
        """Test audio transcription with mocked model."""
        # Create a fake audio file
        audio_file = tmp_path / "test.wav"
        audio_file.write_bytes(b"fake audio content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Hello world, this is a test.",
            "segments": [
                {
                    "id": 0,
                    "start": 0.0,
                    "end": 2.5,
                    "text": " Hello world,",
                    "words": [
                        {"word": "Hello", "start": 0.0, "end": 0.5},
                        {"word": "world,", "start": 0.5, "end": 1.0},
                    ],
                },
                {
                    "id": 1,
                    "start": 2.5,
                    "end": 5.0,
                    "text": " this is a test.",
                    "words": [
                        {"word": "this", "start": 2.5, "end": 3.0},
                        {"word": "is", "start": 3.0, "end": 3.2},
                        {"word": "a", "start": 3.2, "end": 3.4},
                        {"word": "test.", "start": 3.4, "end": 5.0},
                    ],
                },
            ],
            "language": "en",
        }

        self.service._model = mock_model

        result = self.service.transcribe(str(audio_file), file_type="audio")

        assert result["text"] == "Hello world, this is a test."
        assert len(result["segments"]) == 2
        assert result["segments"][0]["start"] == 0.0
        assert result["segments"][0]["end"] == 2.5
        assert result["duration"] == 5.0
        assert result["language"] == "en"
        assert "words" in result["segments"][0]
        assert len(result["segments"][0]["words"]) == 2

    def test_transcribe_video(self, tmp_path):
        """Test video transcription extracts audio first."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "Video transcript.",
            "segments": [
                {"id": 0, "start": 0.0, "end": 3.0, "text": " Video transcript.", "words": []},
            ],
            "language": "en",
        }
        self.service._model = mock_model

        with patch.object(self.service, "extract_audio_from_video") as mock_extract:
            audio_path = tmp_path / "test_audio.wav"
            audio_path.write_bytes(b"extracted audio")
            mock_extract.return_value = str(audio_path)

            result = self.service.transcribe(str(video_file), file_type="video")

        mock_extract.assert_called_once()
        assert result["text"] == "Video transcript."

    def test_transcribe_file_not_found(self):
        """Test transcription with non-existent file raises error."""
        with pytest.raises(FileNotFoundError):
            self.service.transcribe("/nonexistent/file.wav", file_type="audio")

    def test_extract_audio_from_video(self, tmp_path):
        """Test audio extraction from video with mocked ffmpeg."""
        video_file = tmp_path / "test.mp4"
        video_file.write_bytes(b"fake video content")

        with patch("app.services.whisper_service.ffmpeg") as mock_ffmpeg:
            mock_stream = MagicMock()
            mock_ffmpeg.input.return_value = mock_stream
            mock_stream.output.return_value = mock_stream
            mock_stream.overwrite_output.return_value = mock_stream
            mock_stream.run.return_value = (b"", b"")

            with patch("app.services.whisper_service.get_upload_dir", return_value=tmp_path):
                result = self.service.extract_audio_from_video(str(video_file))

        assert "audio.wav" in result

    def test_lazy_model_loading(self):
        """Test model is not loaded until accessed."""
        service = WhisperService()
        assert service._model is None

        with patch("app.services.whisper_service.whisper") as mock_whisper:
            mock_whisper.load_model.return_value = MagicMock()
            _ = service.model
            mock_whisper.load_model.assert_called_once_with("base")

    def test_transcribe_empty_segments(self, tmp_path):
        """Test transcription with no segments."""
        audio_file = tmp_path / "silent.wav"
        audio_file.write_bytes(b"silent audio")

        mock_model = MagicMock()
        mock_model.transcribe.return_value = {
            "text": "",
            "segments": [],
            "language": "en",
        }
        self.service._model = mock_model

        result = self.service.transcribe(str(audio_file), file_type="audio")
        assert result["text"] == ""
        assert result["segments"] == []
        assert result["duration"] == 0.0
