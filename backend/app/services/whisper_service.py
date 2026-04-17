"""Audio/video transcription service using Whisper."""

import logging
import tempfile
from pathlib import Path

import ffmpeg
import whisper

from app.utils.file_utils import get_upload_dir

logger = logging.getLogger(__name__)


class WhisperService:
    """Service for transcribing audio and video files using OpenAI Whisper."""

    def __init__(self):
        self._model = None
        self._model_name = "base"

    @property
    def model(self):
        """Lazy-load the Whisper model."""
        if self._model is None:
            logger.info(f"Loading Whisper model: {self._model_name}")
            self._model = whisper.load_model(self._model_name)
            logger.info("Whisper model loaded successfully")
        return self._model

    def extract_audio_from_video(self, video_path: str | Path) -> str:
        """
        Extract audio track from a video file using ffmpeg.

        Args:
            video_path: Path to the video file.

        Returns:
            Path to the extracted audio file (WAV).
        """
        video_path = Path(video_path)
        if not video_path.exists():
            raise FileNotFoundError(f"Video file not found: {video_path}")

        # Create temp audio file
        audio_dir = get_upload_dir() / "temp_audio"
        audio_dir.mkdir(parents=True, exist_ok=True)
        audio_path = audio_dir / f"{video_path.stem}_audio.wav"

        try:
            (
                ffmpeg
                .input(str(video_path))
                .output(
                    str(audio_path),
                    acodec="pcm_s16le",
                    ar="16000",
                    ac=1,
                )
                .overwrite_output()
                .run(capture_stdout=True, capture_stderr=True)
            )
        except ffmpeg.Error as e:
            logger.error(f"FFmpeg error extracting audio: {e.stderr.decode() if e.stderr else str(e)}")
            raise RuntimeError(f"Failed to extract audio from video: {e}")

        logger.info(f"Extracted audio to {audio_path}")
        return str(audio_path)

    def transcribe(
        self,
        file_path: str | Path,
        file_type: str = "audio",
    ) -> dict:
        """
        Transcribe an audio or video file.

        Args:
            file_path: Path to the audio/video file.
            file_type: Either 'audio' or 'video'.

        Returns:
            Dict with 'text' (full transcript), 'segments' (with timestamps),
            and 'duration' (total duration in seconds).
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        # Extract audio from video if needed
        audio_path = str(file_path)
        temp_audio = None
        if file_type == "video":
            audio_path = self.extract_audio_from_video(file_path)
            temp_audio = audio_path

        try:
            logger.info(f"Starting transcription of {file_path.name}")
            result = self.model.transcribe(
                audio_path,
                word_timestamps=True,
                verbose=False,
            )

            # Process segments with timestamps
            segments = []
            for segment in result.get("segments", []):
                processed_segment = {
                    "id": segment.get("id", 0),
                    "start": round(segment.get("start", 0), 2),
                    "end": round(segment.get("end", 0), 2),
                    "text": segment.get("text", "").strip(),
                }

                # Include word-level timestamps if available
                words = []
                for word_info in segment.get("words", []):
                    words.append({
                        "word": word_info.get("word", "").strip(),
                        "start": round(word_info.get("start", 0), 2),
                        "end": round(word_info.get("end", 0), 2),
                    })
                if words:
                    processed_segment["words"] = words

                segments.append(processed_segment)

            # Calculate duration
            duration = 0.0
            if segments:
                duration = segments[-1]["end"]

            transcript_data = {
                "text": result.get("text", "").strip(),
                "segments": segments,
                "duration": duration,
                "language": result.get("language", "en"),
            }

            logger.info(
                f"Transcription complete: {len(segments)} segments, "
                f"{duration:.1f}s duration, language={transcript_data['language']}"
            )
            return transcript_data

        finally:
            # Clean up temporary audio file
            if temp_audio and Path(temp_audio).exists():
                try:
                    Path(temp_audio).unlink()
                except OSError:
                    pass

    @staticmethod
    def format_timestamp(seconds: float) -> str:
        """Format seconds into HH:MM:SS or MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)

        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


whisper_service = WhisperService()
