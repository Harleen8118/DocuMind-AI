"""Smart Highlight Reel generation service."""

import json
import logging

from app.services.gemini_service import gemini_service

logger = logging.getLogger(__name__)


class HighlightService:
    """
    Service for generating Smart Highlight Reels from video/audio transcripts.

    Orchestrates Gemini AI to identify the top 5 most important moments
    in a transcript, producing clickable timestamp cards.
    """

    async def generate_highlights(
        self,
        transcript_text: str,
        segments: list[dict],
        duration: float = 0.0,
    ) -> list[dict]:
        """
        Generate a Smart Highlight Reel from transcript data.

        Args:
            transcript_text: Full transcript text.
            segments: List of transcript segments with timestamps.
            duration: Total duration of the media in seconds.

        Returns:
            List of highlight dicts, each with:
                - timestamp (float): Start time in seconds
                - timestamp_formatted (str): Human-readable time
                - summary (str): One-line description
                - importance_score (float): 0.0-1.0 rating
        """
        if not segments:
            logger.warning("No segments provided for highlight generation")
            return []

        try:
            highlights = await gemini_service.generate_highlights(
                transcript_text=transcript_text,
                segments=segments,
            )

            # Validate timestamps against actual duration
            if duration > 0:
                highlights = [
                    h for h in highlights
                    if 0 <= h["timestamp"] <= duration
                ]

            # Ensure we have at most 5 highlights
            if len(highlights) > 5:
                # Sort by importance and take top 5
                highlights.sort(key=lambda x: x.get("importance_score", 0), reverse=True)
                highlights = highlights[:5]
                # Re-sort by timestamp for display
                highlights.sort(key=lambda x: x["timestamp"])

            logger.info(f"Generated {len(highlights)} highlights")
            return highlights

        except Exception as e:
            logger.error(f"Error generating highlights: {e}")
            return []

    @staticmethod
    def highlights_to_json(highlights: list[dict]) -> str:
        """Serialize highlights list to JSON string for storage."""
        return json.dumps(highlights, default=str)

    @staticmethod
    def highlights_from_json(json_str: str | None) -> list[dict]:
        """Deserialize highlights from JSON string."""
        if not json_str:
            return []
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return []


highlight_service = HighlightService()
