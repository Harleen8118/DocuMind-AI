"""Vector embedding and semantic search service using FAISS + sentence-transformers."""

import logging
import os
import pickle
from pathlib import Path
from typing import Optional

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer

from app.config import settings

logger = logging.getLogger(__name__)


class VectorService:
    """Service for managing FAISS vector index and semantic search."""

    def __init__(self):
        self._model: Optional[SentenceTransformer] = None
        self._model_name = "all-MiniLM-L6-v2"
        self._dimension = 384  # all-MiniLM-L6-v2 output dimension
        self._index: Optional[faiss.IndexIDMap] = None
        self._metadata: dict = {}  # id -> {doc_id, chunk_index, text, page_number}
        self._next_id: int = 0
        self._index_path = Path(settings.UPLOAD_DIR) / "faiss_index"

    @property
    def model(self) -> SentenceTransformer:
        """Lazy-load the sentence transformer model."""
        if self._model is None:
            logger.info(f"Loading sentence transformer model: {self._model_name}")
            self._model = SentenceTransformer(self._model_name)
            logger.info("Sentence transformer model loaded")
        return self._model

    def initialize(self):
        """Initialize or load the FAISS index."""
        self._index_path.mkdir(parents=True, exist_ok=True)

        index_file = self._index_path / "index.faiss"
        meta_file = self._index_path / "metadata.pkl"

        if index_file.exists() and meta_file.exists():
            try:
                self._index = faiss.read_index(str(index_file))
                with open(meta_file, "rb") as f:
                    saved = pickle.load(f)
                    self._metadata = saved.get("metadata", {})
                    self._next_id = saved.get("next_id", 0)
                logger.info(
                    f"Loaded FAISS index with {self._index.ntotal} vectors"
                )
                return
            except Exception as e:
                logger.warning(f"Could not load existing index: {e}")

        # Create new index
        base_index = faiss.IndexFlatIP(self._dimension)  # Inner product (cosine sim with normalized vectors)
        self._index = faiss.IndexIDMap(base_index)
        self._metadata = {}
        self._next_id = 0
        logger.info("Created new FAISS index")

    def _save_index(self):
        """Persist the FAISS index and metadata to disk."""
        if self._index is None:
            return

        self._index_path.mkdir(parents=True, exist_ok=True)
        faiss.write_index(self._index, str(self._index_path / "index.faiss"))
        with open(self._index_path / "metadata.pkl", "wb") as f:
            pickle.dump(
                {"metadata": self._metadata, "next_id": self._next_id}, f
            )

    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> list[str]:
        """Split text into overlapping chunks."""
        if not text:
            return []

        words = text.split()
        chunks = []
        start = 0

        while start < len(words):
            end = start + chunk_size
            chunk = " ".join(words[start:end])
            if chunk.strip():
                chunks.append(chunk.strip())
            start += chunk_size - overlap

        return chunks

    def add_document(
        self,
        doc_id: str,
        text: str,
        page_numbers: list[int] | None = None,
        segments: list[dict] | None = None,
    ) -> int:
        """
        Add a document's text to the FAISS index.

        Args:
            doc_id: Unique document identifier.
            text: Full document text.
            page_numbers: Optional page numbers for PDF pages.
            segments: Optional transcript segments with timestamps.

        Returns:
            Number of chunks added.
        """
        if self._index is None:
            self.initialize()

        # Remove existing document vectors first
        self.remove_document(doc_id)

        chunks = []
        chunk_metadata = []

        if segments:
            # For audio/video: each segment is a chunk
            for i, seg in enumerate(segments):
                seg_text = seg.get("text", "").strip()
                if seg_text:
                    chunks.append(seg_text)
                    chunk_metadata.append({
                        "doc_id": doc_id,
                        "chunk_index": i,
                        "text": seg_text,
                        "start_time": seg.get("start", 0),
                        "end_time": seg.get("end", 0),
                    })
        else:
            # For PDFs/text: chunk the full text
            text_chunks = self._chunk_text(text)
            for i, chunk in enumerate(text_chunks):
                chunks.append(chunk)
                meta = {
                    "doc_id": doc_id,
                    "chunk_index": i,
                    "text": chunk,
                }
                if page_numbers and i < len(page_numbers):
                    meta["page_number"] = page_numbers[i]
                chunk_metadata.append(meta)

        if not chunks:
            logger.warning(f"No text chunks to index for document {doc_id}")
            return 0

        # Generate embeddings
        embeddings = self.model.encode(chunks, normalize_embeddings=True)
        embeddings = np.array(embeddings, dtype=np.float32)

        # Assign IDs and add to index
        ids = np.array(
            [self._next_id + i for i in range(len(chunks))], dtype=np.int64
        )

        self._index.add_with_ids(embeddings, ids)

        for i, vec_id in enumerate(ids):
            self._metadata[int(vec_id)] = chunk_metadata[i]

        self._next_id += len(chunks)
        self._save_index()

        logger.info(f"Added {len(chunks)} chunks for document {doc_id}")
        return len(chunks)

    def remove_document(self, doc_id: str) -> int:
        """Remove all vectors for a document from the index."""
        if self._index is None or not self._metadata:
            return 0

        ids_to_remove = [
            vec_id
            for vec_id, meta in self._metadata.items()
            if meta.get("doc_id") == doc_id
        ]

        if not ids_to_remove:
            return 0

        try:
            id_array = np.array(ids_to_remove, dtype=np.int64)
            self._index.remove_ids(id_array)
        except Exception as e:
            logger.warning(f"Error removing vectors: {e}")

        for vec_id in ids_to_remove:
            del self._metadata[vec_id]

        self._save_index()
        logger.info(f"Removed {len(ids_to_remove)} vectors for document {doc_id}")
        return len(ids_to_remove)

    def search(
        self,
        query: str,
        doc_id: str | None = None,
        top_k: int = 5,
    ) -> list[dict]:
        """
        Perform semantic search on the index.

        Args:
            query: Search query text.
            doc_id: Optional document ID to filter results.
            top_k: Number of top results to return.

        Returns:
            List of dicts with 'text', 'score', 'doc_id', and optional metadata.
        """
        if self._index is None or self._index.ntotal == 0:
            return []

        # Encode query
        query_embedding = self.model.encode(
            [query], normalize_embeddings=True
        )
        query_embedding = np.array(query_embedding, dtype=np.float32)

        # Search (get more results if filtering by doc_id)
        search_k = top_k * 5 if doc_id else top_k
        scores, ids = self._index.search(query_embedding, min(search_k, self._index.ntotal))

        results = []
        for score, vec_id in zip(scores[0], ids[0]):
            if vec_id == -1:
                continue

            meta = self._metadata.get(int(vec_id))
            if meta is None:
                continue

            # Filter by document if specified
            if doc_id and meta.get("doc_id") != doc_id:
                continue

            result = {
                "text": meta["text"],
                "score": float(score),
                "doc_id": meta["doc_id"],
                "chunk_index": meta.get("chunk_index"),
            }

            if "page_number" in meta:
                result["page_number"] = meta["page_number"]
            if "start_time" in meta:
                result["start_time"] = meta["start_time"]
                result["end_time"] = meta.get("end_time", 0)

            results.append(result)

            if len(results) >= top_k:
                break

        return results


vector_service = VectorService()
