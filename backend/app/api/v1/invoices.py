import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile

from app.dependencies import get_invoice_service
from app.schemas.invoice import InvoiceDetail, InvoiceListParams, InvoiceListResponse, InvoiceUploadResponse
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


@router.get("", response_model=InvoiceListResponse)
def list_invoices(
    params: Annotated[InvoiceListParams, Query()],
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceListResponse:
    """List invoices with filters, free-text search, and pagination."""
    return service.list_invoices(params)


# Registered before /{invoice_id} so these static paths aren't swallowed by the
# dynamic route (FastAPI/Starlette matches routes in registration order).
@router.get("/vendors", response_model=list[str])
def list_vendors(service: InvoiceService = Depends(get_invoice_service)) -> list[str]:
    """Distinct vendor names, for filter dropdowns."""
    return service.list_vendors()


@router.get("/materials", response_model=list[str])
def list_materials(service: InvoiceService = Depends(get_invoice_service)) -> list[str]:
    """Distinct material types, for filter dropdowns."""
    return service.list_materials()


@router.get("/{invoice_id}", response_model=InvoiceDetail)
def get_invoice(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceDetail:
    """Full invoice detail, including line items, raw text, and structured JSON."""
    return service.get_invoice(invoice_id)
