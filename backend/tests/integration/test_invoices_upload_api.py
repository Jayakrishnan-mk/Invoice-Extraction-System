from decimal import Decimal
from pathlib import Path

from app.core.exceptions import AIExtractionError
from app.models.invoice import Invoice
from app.schemas.extraction import ExtractedInvoiceData

MOCK_INBOX = Path(__file__).resolve().parents[2] / "mock_inbox"
SAMPLE_PDF = MOCK_INBOX / "INV-CEM-1001.pdf"

VALID_PAYLOAD = {
    "vendor_name": "ABC Cement Pvt Ltd",
    "invoice_number": "INV-CEM-1001",
    "invoice_date": "2026-08-01",
    "material_type": "Cement",
    "items": [
        {
            "description": "OPC 53 Grade Cement",
            "quantity": "250",
            "unit": "Bags",
            "unit_price": "420.00",
            "line_total": "105000.00",
        }
    ],
    "subtotal_amount": "105000.00",
    "tax_amount": "18900.00",
    "total_amount": "123900.00",
    "currency": "INR",
    "payment_status": "unpaid",
}


class TestUploadInvoices:
    def test_upload_succeeds_and_persists_invoice(self, client, db_session, mock_ai_service):
        mock_ai_service.extract.return_value = ExtractedInvoiceData.model_validate(VALID_PAYLOAD)

        with open(SAMPLE_PDF, "rb") as f:
            response = client.post(
                "/api/v1/invoices/upload",
                files=[("files", ("INV-CEM-1001.pdf", f, "application/pdf"))],
            )

        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 1

        result = results[0]
        assert result["status"] == "completed"
        assert result["error"] is None
        assert result["invoice"]["vendor_name"] == "ABC Cement Pvt Ltd"
        assert result["invoice"]["invoice_number"] == "INV-CEM-1001"
        assert Decimal(result["invoice"]["total_amount"]) == Decimal("123900.00")
        assert len(result["invoice"]["items"]) == 1
        assert result["invoice"]["items"][0]["description"] == "OPC 53 Grade Cement"

        assert (
            db_session.query(Invoice).filter(Invoice.invoice_number == "INV-CEM-1001").count() == 1
        )

    def test_upload_batch_partial_failure_does_not_persist_failed_file(
        self, client, db_session, mock_ai_service
    ):
        mock_ai_service.extract.return_value = ExtractedInvoiceData.model_validate(VALID_PAYLOAD)

        with open(SAMPLE_PDF, "rb") as good_file:
            response = client.post(
                "/api/v1/invoices/upload",
                files=[
                    ("files", ("INV-CEM-1001.pdf", good_file, "application/pdf")),
                    ("files", ("corrupt.pdf", b"not a real pdf", "application/pdf")),
                ],
            )

        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 2

        assert results[0]["status"] == "completed"
        assert results[1]["status"] == "failed"
        assert results[1]["invoice"] is None
        assert results[1]["error"]

        assert (
            db_session.query(Invoice).filter(Invoice.invoice_number == "INV-CEM-1001").count() == 1
        )

    def test_upload_rejects_non_pdf_file(self, client, mock_ai_service):
        response = client.post(
            "/api/v1/invoices/upload",
            files=[("files", ("notes.txt", b"hello", "text/plain"))],
        )

        assert response.status_code == 200
        result = response.json()["results"][0]
        assert result["status"] == "failed"
        assert "not a PDF" in result["error"]
        mock_ai_service.extract.assert_not_called()

    def test_upload_reports_ai_extraction_failure_without_persisting(
        self, client, db_session, mock_ai_service
    ):
        mock_ai_service.extract.side_effect = AIExtractionError("Gemini is down")

        with open(SAMPLE_PDF, "rb") as f:
            response = client.post(
                "/api/v1/invoices/upload",
                files=[("files", ("INV-CEM-1001.pdf", f, "application/pdf"))],
            )

        assert response.status_code == 200
        result = response.json()["results"][0]
        assert result["status"] == "failed"
        assert result["error"] == "Gemini is down"
        assert db_session.query(Invoice).filter(Invoice.invoice_number == "INV-CEM-1001").count() == 0


class TestIngestMockInbox:
    def test_ingest_mock_inbox_processes_every_pdf(self, client, db_session, mock_ai_service):
        mock_ai_service.extract.return_value = ExtractedInvoiceData.model_validate(VALID_PAYLOAD)

        response = client.post("/api/v1/invoices/ingest-mock")

        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == len(list(MOCK_INBOX.glob("*.pdf")))
        assert all(r["status"] == "completed" for r in results)
