"""Tests for PDF extraction service."""

import os
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from app.services.pdf_service import PDFService


class TestPDFService:
    """Tests for PDFService."""

    def setup_method(self):
        """Create a fresh service instance."""
        self.service = PDFService()

    def test_extract_text(self, tmp_path):
        """Test PDF text extraction with mocked PyMuPDF."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf content")

        mock_page1 = MagicMock()
        mock_page1.get_text.return_value = "Page 1 content about AI."
        mock_page2 = MagicMock()
        mock_page2.get_text.return_value = "Page 2 discusses machine learning."
        mock_page3 = MagicMock()
        mock_page3.get_text.return_value = ""  # Empty page

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=3)
        mock_doc.__getitem__ = MagicMock(side_effect=[mock_page1, mock_page2, mock_page3])

        with patch("app.services.pdf_service.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            pages = self.service.extract_text(pdf_path)

        assert len(pages) == 2  # Empty page excluded
        assert pages[0]["page_number"] == 1
        assert "AI" in pages[0]["text"]
        assert pages[1]["page_number"] == 2
        assert "machine learning" in pages[1]["text"]

    def test_extract_text_file_not_found(self):
        """Test extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.service.extract_text("/nonexistent/file.pdf")

    def test_get_full_text(self):
        """Test combining pages into full text."""
        pages = [
            {"page_number": 1, "text": "First page"},
            {"page_number": 2, "text": "Second page"},
        ]
        result = PDFService.get_full_text(pages)
        assert "[Page 1]" in result
        assert "First page" in result
        assert "[Page 2]" in result
        assert "Second page" in result

    def test_get_page_count(self, tmp_path):
        """Test getting page count."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=5)

        with patch("app.services.pdf_service.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc

            count = self.service.get_page_count(pdf_path)

        assert count == 5

    def test_extract_images(self, tmp_path):
        """Test image extraction from PDF."""
        pdf_path = tmp_path / "test.pdf"
        pdf_path.write_bytes(b"fake pdf")

        mock_page = MagicMock()
        mock_page.get_images.return_value = [(1, 0, 0, 0, 0, 0, 0)]

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)
        mock_doc.extract_image.return_value = {
            "image": b"fake image bytes",
            "ext": "png",
        }

        with patch("app.services.pdf_service.fitz") as mock_fitz, \
             patch("app.services.pdf_service.get_upload_dir", return_value=tmp_path):
            mock_fitz.open.return_value = mock_doc

            images = self.service.extract_images(pdf_path, "test-doc-id")

        assert len(images) == 1
        assert "png" in images[0]

    def test_extract_images_file_not_found(self):
        """Test image extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.service.extract_images("/nonexistent/file.pdf", "doc-id")

    def test_extract_text_empty_pdf(self, tmp_path):
        """Test extracting text from PDF with only empty pages."""
        pdf_path = tmp_path / "empty.pdf"
        pdf_path.write_bytes(b"fake pdf")

        mock_page = MagicMock()
        mock_page.get_text.return_value = "   \n  "

        mock_doc = MagicMock()
        mock_doc.__len__ = MagicMock(return_value=1)
        mock_doc.__getitem__ = MagicMock(return_value=mock_page)

        with patch("app.services.pdf_service.fitz") as mock_fitz:
            mock_fitz.open.return_value = mock_doc
            pages = self.service.extract_text(pdf_path)

        assert len(pages) == 0
