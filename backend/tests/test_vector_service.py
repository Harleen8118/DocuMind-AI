"""Tests for vector embedding and search service."""

from unittest.mock import patch, MagicMock

import numpy as np
import pytest

from app.services.vector_service import VectorService


class TestVectorService:
    """Tests for VectorService."""

    def setup_method(self):
        """Create a fresh service instance with mocked model."""
        self.service = VectorService()
        # Mock the sentence transformer
        self.mock_model = MagicMock()
        self.service._model = self.mock_model

    def test_initialize_new_index(self, tmp_path):
        """Test creating a new FAISS index."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        assert self.service._index is not None
        assert self.service._index.ntotal == 0

    def test_chunk_text(self):
        """Test text chunking."""
        text = " ".join([f"word{i}" for i in range(1000)])
        chunks = self.service._chunk_text(text, chunk_size=100, overlap=10)

        assert len(chunks) > 1
        # Verify overlap: last words of first chunk should be in second chunk
        first_words = set(chunks[0].split()[-10:])
        second_words = set(chunks[1].split()[:10])
        assert len(first_words & second_words) > 0

    def test_chunk_text_short(self):
        """Test chunking short text produces single chunk."""
        chunks = self.service._chunk_text("short text", chunk_size=100)
        assert len(chunks) == 1
        assert chunks[0] == "short text"

    def test_chunk_text_empty(self):
        """Test chunking empty text returns empty list."""
        assert self.service._chunk_text("") == []

    def test_add_document(self, tmp_path):
        """Test adding a document to the index."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        # Mock encoder to return predictable embeddings
        self.mock_model.encode.return_value = np.random.rand(3, 384).astype(np.float32)

        count = self.service.add_document(
            doc_id="doc1",
            text="This is the first document about machine learning and artificial intelligence.",
        )

        assert count > 0
        assert self.service._index.ntotal > 0
        assert any(m["doc_id"] == "doc1" for m in self.service._metadata.values())

    def test_add_document_with_segments(self, tmp_path):
        """Test adding a document with transcript segments."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        segments = [
            {"text": "First segment", "start": 0.0, "end": 5.0},
            {"text": "Second segment", "start": 5.0, "end": 10.0},
        ]
        self.mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)

        count = self.service.add_document(
            doc_id="audio1",
            text="First segment Second segment",
            segments=segments,
        )

        assert count == 2
        # Verify timestamps are stored
        meta_values = list(self.service._metadata.values())
        assert any(m.get("start_time") == 0.0 for m in meta_values)

    def test_search(self, tmp_path):
        """Test semantic search."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        # Add a document
        doc_embedding = np.random.rand(2, 384).astype(np.float32)
        # Normalize
        norms = np.linalg.norm(doc_embedding, axis=1, keepdims=True)
        doc_embedding = doc_embedding / norms

        self.mock_model.encode.return_value = doc_embedding

        self.service.add_document(
            doc_id="doc1",
            text="Machine learning is great. Deep learning is a subset.",
        )

        # Search
        query_embedding = np.random.rand(1, 384).astype(np.float32)
        query_embedding = query_embedding / np.linalg.norm(query_embedding)
        self.mock_model.encode.return_value = query_embedding

        results = self.service.search("machine learning", top_k=2)

        assert len(results) > 0
        assert "text" in results[0]
        assert "score" in results[0]
        assert "doc_id" in results[0]

    def test_search_filter_by_doc_id(self, tmp_path):
        """Test search filtered by document ID."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        # Add two documents
        self.mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        self.service.add_document(doc_id="doc1", text="Document one content")

        self.mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        self.service.add_document(doc_id="doc2", text="Document two content")

        # Search only in doc1
        self.mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        results = self.service.search("content", doc_id="doc1", top_k=5)

        assert all(r["doc_id"] == "doc1" for r in results)

    def test_remove_document(self, tmp_path):
        """Test removing a document from the index."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        self.mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        self.service.add_document(doc_id="doc1", text="Test content")

        initial_count = self.service._index.ntotal
        removed = self.service.remove_document("doc1")

        assert removed > 0
        assert self.service._index.ntotal < initial_count
        assert not any(m["doc_id"] == "doc1" for m in self.service._metadata.values())

    def test_remove_nonexistent_document(self, tmp_path):
        """Test removing a document that doesn't exist."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()
        removed = self.service.remove_document("nonexistent")
        assert removed == 0

    def test_search_empty_index(self, tmp_path):
        """Test searching an empty index."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        self.mock_model.encode.return_value = np.random.rand(1, 384).astype(np.float32)
        results = self.service.search("anything")
        assert results == []

    def test_save_and_load_index(self, tmp_path):
        """Test index persistence."""
        self.service._index_path = tmp_path / "faiss"
        self.service.initialize()

        self.mock_model.encode.return_value = np.random.rand(2, 384).astype(np.float32)
        self.service.add_document(doc_id="persistent", text="Test persistence of index data")

        # Create new service and load
        new_service = VectorService()
        new_service._index_path = tmp_path / "faiss"
        new_service._model = self.mock_model
        new_service.initialize()

        assert new_service._index.ntotal > 0
        assert any(m["doc_id"] == "persistent" for m in new_service._metadata.values())
