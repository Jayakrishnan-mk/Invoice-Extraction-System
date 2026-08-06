from fastapi import APIRouter, Depends, File, UploadFile

from app.dependencies import get_invoice_service
from app.schemas.invoice import InvoiceUploadResponse
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])


@router.post("/upload", response_model=InvoiceUploadResponse)
def upload_invoices(
    files: list[UploadFile] = File(...),
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceUploadResponse:
    """Upload one or more invoice PDFs. Each file succeeds or fails independently."""
    return InvoiceUploadResponse(results=service.upload_files(files))


@router.post("/ingest-mock", response_model=InvoiceUploadResponse)
def ingest_mock_inbox(
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceUploadResponse:
    """Process every PDF currently in the mock inbox, simulating email ingestion."""
    return InvoiceUploadResponse(results=service.ingest_mock_inbox())
