import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, File, Query, UploadFile, status

from app.config import settings
from app.dependencies import get_invoice_service
from app.schemas.common import ErrorResponse
from app.schemas.invoice import InvoiceDetail, InvoiceListParams, InvoiceListResponse, InvoiceUploadResponse
from app.services.invoice_service import InvoiceService

router = APIRouter(prefix="/invoices", tags=["invoices"])

_UPLOAD_DESCRIPTION = f"""
Upload one or more invoice PDFs for AI extraction.

Each file is processed independently: text is pulled from the PDF, sent to Gemini for
structured extraction, validated, and persisted. A failure at any step for one file
(bad file type, empty file, over the {settings.MAX_UPLOAD_SIZE_MB}MB limit, unreadable
PDF, extraction error, etc.) does not affect the other files in the batch and does not
raise an HTTP error — the response is always `200 OK`, with per-file success or
failure reported in `results`.
"""


@router.post(
    "/upload",
    response_model=InvoiceUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload invoice PDFs",
    description=_UPLOAD_DESCRIPTION,
)
def upload_invoices(
    files: list[UploadFile] = File(..., description="One or more PDF invoices."),
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceUploadResponse:
    return InvoiceUploadResponse(results=service.upload_files(files))


@router.post(
    "/ingest-mock",
    response_model=InvoiceUploadResponse,
    status_code=status.HTTP_200_OK,
    summary="Ingest the mock inbox",
    description="Process every PDF currently in `MOCK_INBOX_DIR`, simulating incoming "
    "vendor emails. Same per-file success/failure semantics as `/invoices/upload`.",
)
def ingest_mock_inbox(
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceUploadResponse:
    return InvoiceUploadResponse(results=service.ingest_mock_inbox())


@router.get(
    "",
    response_model=InvoiceListResponse,
    summary="List invoices",
    description="List invoices with filters, free-text search, and pagination. "
    "All filters are optional and combine with AND.",
)
def list_invoices(
    params: Annotated[InvoiceListParams, Query()],
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceListResponse:
    return service.list_invoices(params)


# Registered before /{invoice_id} so these static paths aren't swallowed by the
# dynamic route (FastAPI/Starlette matches routes in registration order).
@router.get(
    "/vendors",
    response_model=list[str],
    summary="List distinct vendor names",
    description="Distinct vendor names across all invoices, for filter dropdowns.",
)
def list_vendors(service: InvoiceService = Depends(get_invoice_service)) -> list[str]:
    return service.list_vendors()


@router.get(
    "/materials",
    response_model=list[str],
    summary="List distinct material types",
    description="Distinct material types across all invoices, for filter dropdowns.",
)
def list_materials(service: InvoiceService = Depends(get_invoice_service)) -> list[str]:
    return service.list_materials()


@router.get(
    "/{invoice_id}",
    response_model=InvoiceDetail,
    summary="Get invoice detail",
    description="Full invoice detail, including line items, raw extracted text, and "
    "the full structured JSON returned by Gemini.",
    responses={status.HTTP_404_NOT_FOUND: {"model": ErrorResponse, "description": "Invoice not found"}},
)
def get_invoice(
    invoice_id: uuid.UUID,
    service: InvoiceService = Depends(get_invoice_service),
) -> InvoiceDetail:
    return service.get_invoice(invoice_id)
