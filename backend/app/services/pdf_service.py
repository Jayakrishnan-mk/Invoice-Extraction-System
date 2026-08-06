import logging
from pathlib import Path

import fitz
import pdfplumber

from app.core.exceptions import PDFExtractionError

logger = logging.getLogger(__name__)


class PDFService:
    """Extracts raw text from invoice PDFs.

    Tries pdfplumber first; falls back to PyMuPDF for PDFs pdfplumber can't
    pull a text layer from. Raises PDFExtractionError if neither yields text
    (e.g. a scanned image with no text layer) - OCR is out of scope.
    """

    def extract_text(self, file_path: str | Path) -> str:
        text = self._extract_with_pdfplumber(file_path)

        if not text:
            logger.info("pdfplumber found no text layer in %s, falling back to PyMuPDF", file_path)
            text = self._extract_with_pymupdf(file_path)

        if not text:
            raise PDFExtractionError(f"No extractable text found in PDF: {Path(file_path).name}")

        return text

    def _extract_with_pdfplumber(self, file_path: str | Path) -> str:
        try:
            with pdfplumber.open(file_path) as pdf:
                pages = [page.extract_text() or "" for page in pdf.pages]
        except Exception:
            logger.exception("pdfplumber failed to read %s", file_path)
            return ""

        return "\n".join(page for page in pages if page).strip()

    def _extract_with_pymupdf(self, file_path: str | Path) -> str:
        try:
            with fitz.open(file_path) as doc:
                pages = [page.get_text() or "" for page in doc]
        except Exception:
            logger.exception("PyMuPDF failed to read %s", file_path)
            return ""

        return "\n".join(page for page in pages if page).strip()
