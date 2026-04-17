"""Google Gemini AI service for chat, summarization, and highlight generation."""

import json
import logging
from typing import AsyncGenerator

import google.generativeai as genai

from app.config import settings

logger = logging.getLogger(__name__)


class GeminiService:
    """Service for all Google Gemini API interactions."""

    def __init__(self):
        self._configured = False
        self._model = None

    def _ensure_configured(self):
        """Configure the Gemini API if not already done."""
        if not self._configured:
            genai.configure(api_key=settings.GEMINI_API_KEY)
            self._model = genai.GenerativeModel("gemini-1.5-flash")
            self._configured = True

    def _get_model(self):
        """Get the configured Gemini model."""
        self._ensure_configured()
        return self._model

    async def chat_with_context(
        self,
        query: str,
        context_chunks: list[dict],
        chat_history: list[dict] | None = None,
        document_type: str = "document",
    ) -> str:
        """
        Chat with context from semantic search results.

        Args:
            query: User's question.
            context_chunks: Relevant text chunks from vector search.
            chat_history: Previous messages in the conversation.
            document_type: Type of document (pdf, audio, video).

        Returns:
            AI response text.
        """
        model = self._get_model()

        # Build context string
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            part = f"[Chunk {i}]"
            if "page_number" in chunk:
                part += f" (Page {chunk['page_number']})"
            if "start_time" in chunk:
                start = self._format_time(chunk["start_time"])
                end = self._format_time(chunk.get("end_time", 0))
                part += f" (Timestamp: {start} - {end})"
            part += f"\n{chunk['text']}"
            context_parts.append(part)

        context_text = "\n\n".join(context_parts)

        # Build prompt
        timestamp_instruction = ""
        if document_type in ("audio", "video"):
            timestamp_instruction = """
When referencing specific moments, include timestamps in the format [MM:SS] or [HH:MM:SS].
Format timestamps as JSON array at the end of your response like:
TIMESTAMPS: [{"time_seconds": 125.5, "time_formatted": "02:05", "label": "brief description"}]
Only include TIMESTAMPS if you reference specific moments in your answer.
"""

        system_prompt = f"""You are DocuMind AI, an intelligent document analysis assistant.
You answer questions about documents based on the provided context.
Be accurate, helpful, and cite specific parts of the document when relevant.
{timestamp_instruction}

CONTEXT FROM DOCUMENT:
{context_text}
"""

        # Build message history
        messages = []
        if chat_history:
            for msg in chat_history[-10:]:  # Last 10 messages for context window
                role = "user" if msg.get("role") == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})

        messages.append({"role": "user", "parts": [query]})

        try:
            chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])
            response = chat.send_message(
                f"{system_prompt}\n\nUser Question: {query}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini chat error: {e}")
            raise

    async def chat_stream(
        self,
        query: str,
        context_chunks: list[dict],
        chat_history: list[dict] | None = None,
        document_type: str = "document",
    ) -> AsyncGenerator[str, None]:
        """
        Stream chat response with context.

        Yields:
            Text chunks as they are generated.
        """
        model = self._get_model()

        # Build context
        context_parts = []
        for i, chunk in enumerate(context_chunks, 1):
            part = f"[Chunk {i}]"
            if "page_number" in chunk:
                part += f" (Page {chunk['page_number']})"
            if "start_time" in chunk:
                start = self._format_time(chunk["start_time"])
                end = self._format_time(chunk.get("end_time", 0))
                part += f" (Timestamp: {start} - {end})"
            part += f"\n{chunk['text']}"
            context_parts.append(part)

        context_text = "\n\n".join(context_parts)

        timestamp_instruction = ""
        if document_type in ("audio", "video"):
            timestamp_instruction = """
When referencing specific moments, include timestamps in the format [MM:SS] or [HH:MM:SS].
Format timestamps as JSON array at the end of your response like:
TIMESTAMPS: [{"time_seconds": 125.5, "time_formatted": "02:05", "label": "brief description"}]
Only include TIMESTAMPS if you reference specific moments in your answer.
"""

        system_prompt = f"""You are DocuMind AI, an intelligent document analysis assistant.
You answer questions about documents based on the provided context.
Be accurate, helpful, and cite specific parts of the document when relevant.
{timestamp_instruction}

CONTEXT FROM DOCUMENT:
{context_text}
"""

        messages = []
        if chat_history:
            for msg in chat_history[-10:]:
                role = "user" if msg.get("role") == "user" else "model"
                messages.append({"role": role, "parts": [msg["content"]]})

        try:
            chat = model.start_chat(history=messages if messages else [])
            response = chat.send_message(
                f"{system_prompt}\n\nUser Question: {query}",
                generation_config=genai.types.GenerationConfig(
                    temperature=0.7,
                    max_output_tokens=2048,
                ),
                stream=True,
            )

            for chunk in response:
                if chunk.text:
                    yield chunk.text

        except Exception as e:
            logger.error(f"Gemini streaming error: {e}")
            yield f"\n\n[Error: {str(e)}]"

    async def summarize_document(self, text: str, document_type: str = "pdf") -> str:
        """
        Generate a comprehensive summary of a document.

        Args:
            text: Full document text or transcript.
            document_type: Type of document.

        Returns:
            Summary text.
        """
        model = self._get_model()

        # Truncate if too long (Gemini has context limits)
        max_chars = 100000
        if len(text) > max_chars:
            text = text[:max_chars] + "\n\n[Content truncated due to length...]"

        type_label = {
            "pdf": "PDF document",
            "audio": "audio recording transcript",
            "video": "video transcript",
        }.get(document_type, "document")

        prompt = f"""Provide a comprehensive summary of this {type_label}.
Include:
1. **Main Topics**: Key subjects covered
2. **Key Points**: The most important takeaways (bullet points)
3. **Details**: Notable details, data, or quotes
4. **Conclusion**: Brief overall assessment

DOCUMENT CONTENT:
{text}"""

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.5,
                    max_output_tokens=2048,
                ),
            )
            return response.text
        except Exception as e:
            logger.error(f"Gemini summarization error: {e}")
            raise

    async def generate_highlights(
        self, transcript_text: str, segments: list[dict]
    ) -> list[dict]:
        """
        Generate Smart Highlight Reel — top 5 important moments.

        Args:
            transcript_text: Full transcript text.
            segments: Transcript segments with timestamps.

        Returns:
            List of highlight dicts with timestamp, summary, importance_score.
        """
        model = self._get_model()

        # Build segment reference
        segment_text = "\n".join(
            f"[{self._format_time(s['start'])} - {self._format_time(s['end'])}] {s['text']}"
            for s in segments
            if s.get("text", "").strip()
        )

        prompt = f"""Analyze this transcript and identify the TOP 5 most important, interesting, or insightful moments.

For each moment, provide:
1. The exact timestamp (start time in seconds)
2. A one-line summary of what happens/is said
3. An importance score from 0.0 to 1.0

Return ONLY valid JSON in this exact format:
[
  {{"timestamp": 45.5, "summary": "Brief description of the key moment", "importance_score": 0.95}},
  {{"timestamp": 120.0, "summary": "Another important moment", "importance_score": 0.88}}
]

TRANSCRIPT WITH TIMESTAMPS:
{segment_text}"""

        try:
            response = model.generate_content(
                prompt,
                generation_config=genai.types.GenerationConfig(
                    temperature=0.3,
                    max_output_tokens=1024,
                ),
            )

            # Parse JSON from response
            response_text = response.text.strip()
            # Handle markdown code blocks
            if "```json" in response_text:
                response_text = response_text.split("```json")[1].split("```")[0]
            elif "```" in response_text:
                response_text = response_text.split("```")[1].split("```")[0]

            highlights = json.loads(response_text.strip())

            # Validate and format
            formatted = []
            for h in highlights[:5]:
                ts = float(h.get("timestamp", 0))
                formatted.append({
                    "timestamp": ts,
                    "timestamp_formatted": self._format_time(ts),
                    "summary": h.get("summary", ""),
                    "importance_score": float(h.get("importance_score", 0.5)),
                })

            # Sort by timestamp
            formatted.sort(key=lambda x: x["timestamp"])
            return formatted

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse Gemini highlights response: {e}")
            return []
        except Exception as e:
            logger.error(f"Gemini highlights generation error: {e}")
            raise

    @staticmethod
    def _format_time(seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS."""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{secs:02d}"
        return f"{minutes:02d}:{secs:02d}"


gemini_service = GeminiService()
