from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import PDFExtractionError
from app.services.pdf_service import PDFService


def _mock_pdfplumber_pdf(page_texts: list[str | None]) -> MagicMock:
    pages = [MagicMock(extract_text=MagicMock(return_value=text)) for text in page_texts]
    pdf = MagicMock()
    pdf.pages = pages
    pdf.__enter__.return_value = pdf
    pdf.__exit__.return_value = False
    return pdf


def _mock_fitz_doc(page_texts: list[str | None]) -> MagicMock:
    pages = [MagicMock(get_text=MagicMock(return_value=text)) for text in page_texts]
    doc = MagicMock()
    doc.__enter__.return_value = doc
    doc.__exit__.return_value = False
    doc.__iter__.return_value = iter(pages)
    return doc


@pytest.fixture
def service() -> PDFService:
    return PDFService()


class TestExtractText:
    def test_uses_pdfplumber_text_when_present(self, service):
        with (
            patch("app.services.pdf_service.pdfplumber.open") as mock_plumber_open,
            patch("app.services.pdf_service.fitz.open") as mock_fitz_open,
        ):
            mock_plumber_open.return_value = _mock_pdfplumber_pdf(["Invoice #123", "Page two"])

            result = service.extract_text("invoice.pdf")

        assert result == "Invoice #123\nPage two"
        mock_fitz_open.assert_not_called()

    def test_skips_blank_pages_when_joining(self, service):
        with patch("app.services.pdf_service.pdfplumber.open") as mock_plumber_open:
            mock_plumber_open.return_value = _mock_pdfplumber_pdf(["First page", "", None, "Last page"])

            result = service.extract_text("invoice.pdf")

        assert result == "First page\nLast page"

    def test_falls_back_to_pymupdf_when_pdfplumber_finds_no_text(self, service):
        with (
            patch("app.services.pdf_service.pdfplumber.open") as mock_plumber_open,
            patch("app.services.pdf_service.fitz.open") as mock_fitz_open,
        ):
            mock_plumber_open.return_value = _mock_pdfplumber_pdf([None, ""])
            mock_fitz_open.return_value = _mock_fitz_doc(["Recovered text"])

            result = service.extract_text("no_text_layer.pdf")

        assert result == "Recovered text"

    def test_falls_back_to_pymupdf_when_pdfplumber_raises(self, service):
        with (
            patch("app.services.pdf_service.pdfplumber.open", side_effect=Exception("corrupt")),
            patch("app.services.pdf_service.fitz.open") as mock_fitz_open,
        ):
            mock_fitz_open.return_value = _mock_fitz_doc(["Recovered text"])

            result = service.extract_text("weird.pdf")

        assert result == "Recovered text"

    def test_raises_when_both_extractors_find_no_text(self, service):
        with (
            patch("app.services.pdf_service.pdfplumber.open") as mock_plumber_open,
            patch("app.services.pdf_service.fitz.open") as mock_fitz_open,
        ):
            mock_plumber_open.return_value = _mock_pdfplumber_pdf([None])
            mock_fitz_open.return_value = _mock_fitz_doc([""])

            with pytest.raises(PDFExtractionError):
                service.extract_text("scanned_image_only.pdf")

    def test_raises_when_both_extractors_raise(self, service):
        with (
            patch("app.services.pdf_service.pdfplumber.open", side_effect=Exception("bad file")),
            patch("app.services.pdf_service.fitz.open", side_effect=Exception("also bad")),
        ):
            with pytest.raises(PDFExtractionError):
                service.extract_text("not_a_pdf.pdf")
