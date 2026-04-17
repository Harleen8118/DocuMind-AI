"""PDF text extraction service using PyMuPDF."""

import logging
from pathlib import Path

import fitz  # PyMuPDF

from app.utils.file_utils import get_upload_dir

logger = logging.getLogger(__name__)


class PDFService:
    """Service for extracting text and images from PDF files."""

    @staticmethod
    def extract_text(file_path: str | Path) -> list[dict]:
        """
        Extract text from a PDF file page by page.

        Args:
            file_path: Path to the PDF file.

        Returns:
            List of dicts with 'page_number' and 'text' keys.
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        pages = []
        try:
            doc = fitz.open(str(file_path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                text = page.get_text("text")
                if text.strip():
                    pages.append({
                        "page_number": page_num + 1,
                        "text": text.strip(),
                    })
            doc.close()
        except Exception as e:
            logger.error(f"Error extracting text from PDF {file_path}: {e}")
            raise

        logger.info(f"Extracted text from {len(pages)} pages of {file_path.name}")
        return pages

    @staticmethod
    def extract_images(file_path: str | Path, document_id: str) -> list[str]:
        """
        Extract embedded images from a PDF and save them to disk.

        Args:
            file_path: Path to the PDF file.
            document_id: Unique document ID for organizing saved images.

        Returns:
            List of saved image file paths (relative to upload dir).
        """
        file_path = Path(file_path)
        if not file_path.exists():
            raise FileNotFoundError(f"PDF file not found: {file_path}")

        image_dir = get_upload_dir() / "images" / document_id
        image_dir.mkdir(parents=True, exist_ok=True)

        saved_images = []
        try:
            doc = fitz.open(str(file_path))
            for page_num in range(len(doc)):
                page = doc[page_num]
                image_list = page.get_images(full=True)

                for img_index, img_info in enumerate(image_list):
                    xref = img_info[0]
                    try:
                        base_image = doc.extract_image(xref)
                        image_bytes = base_image["image"]
                        image_ext = base_image["ext"]

                        image_filename = f"page{page_num + 1}_img{img_index + 1}.{image_ext}"
                        image_path = image_dir / image_filename

                        with open(image_path, "wb") as img_file:
                            img_file.write(image_bytes)

                        relative_path = f"images/{document_id}/{image_filename}"
                        saved_images.append(relative_path)
                    except Exception as e:
                        logger.warning(
                            f"Could not extract image {img_index} from page {page_num + 1}: {e}"
                        )
                        continue

            doc.close()
        except Exception as e:
            logger.error(f"Error extracting images from PDF {file_path}: {e}")
            raise

        logger.info(f"Extracted {len(saved_images)} images from {file_path.name}")
        return saved_images

    @staticmethod
    def get_page_count(file_path: str | Path) -> int:
        """Get the number of pages in a PDF."""
        file_path = Path(file_path)
        doc = fitz.open(str(file_path))
        count = len(doc)
        doc.close()
        return count

    @staticmethod
    def get_full_text(pages: list[dict]) -> str:
        """Combine all page texts into a single string."""
        return "\n\n".join(
            f"[Page {p['page_number']}]\n{p['text']}" for p in pages
        )


pdf_service = PDFService()
