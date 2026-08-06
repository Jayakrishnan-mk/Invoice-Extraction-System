import logging
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile

from app.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.models.invoice import Invoice, PaymentStatus
from app.models.invoice_item import InvoiceItem
from app.repositories.invoice_repository import InvoiceRepository
from app.schemas.extraction import ExtractedInvoiceData
from app.schemas.invoice import InvoiceListItem, InvoiceListParams, InvoiceListResponse, InvoiceUploadResult
from app.services.ai_extraction_service import AIExtractionService
from app.services.pdf_service import PDFService
from app.utils.file_utils import save_pdf, validate_pdf_upload

logger = logging.getLogger(__name__)

_VALID_PAYMENT_STATUSES = {status.value for status in PaymentStatus}


class InvoiceService:
    """Orchestrates upload -> text extraction -> AI extraction -> persistence.

    Synchronous and fail-fast per file (CLAUDE.md "Deliberate simplifications"): a
    failure at any step for one file writes nothing to the DB and does not affect
    the other files in the same batch.
    """

    def __init__(
        self,
        pdf_service: PDFService,
        ai_service: AIExtractionService,
        repository: InvoiceRepository,
    ):
        self._pdf_service = pdf_service
        self._ai_service = ai_service
        self._repository = repository

    def upload_files(self, files: list[UploadFile]) -> list[InvoiceUploadResult]:
        return [self._process_upload(file) for file in files]

    def ingest_mock_inbox(self) -> list[InvoiceUploadResult]:
        inbox = Path(settings.MOCK_INBOX_DIR)
        pdf_paths = sorted(inbox.glob("*.pdf")) if inbox.is_dir() else []

        return [self._process_file(path.read_bytes(), path.name) for path in pdf_paths]

    def list_invoices(self, params: InvoiceListParams) -> InvoiceListResponse:
        invoices, total = self._repository.list_filtered(params)
        items = [InvoiceListItem.model_validate(invoice) for invoice in invoices]
        return InvoiceListResponse.build(items, total, params.page, params.page_size)

    def get_invoice(self, invoice_id: uuid.UUID) -> Invoice:
        invoice = self._repository.get_by_id(invoice_id)
        if invoice is None:
            raise NotFoundError(f"Invoice {invoice_id} not found")
        return invoice

    def list_vendors(self) -> list[str]:
        return self._repository.list_distinct_vendors()

    def list_materials(self) -> list[str]:
        return self._repository.list_distinct_materials()

    def _process_upload(self, file: UploadFile) -> InvoiceUploadResult:
        try:
            content = validate_pdf_upload(file, settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024)
        except AppError as exc:
            logger.warning("Rejected upload %s: %s", file.filename, exc.detail)
            return InvoiceUploadResult(filename=file.filename or "unknown", status="failed", error=exc.detail)

        return self._process_file(content, file.filename or "unknown")

    def _process_file(self, content: bytes, filename: str) -> InvoiceUploadResult:
        started_at = time.monotonic()
        saved_path: Path | None = None
        try:
            saved_path = save_pdf(content, filename, settings.UPLOAD_DIR)
            raw_text = self._pdf_service.extract_text(saved_path)
            extracted = self._ai_service.extract(raw_text)
            processing_time_ms = int((time.monotonic() - started_at) * 1000)

            invoice = self._build_invoice(
                extracted=extracted,
                raw_text=raw_text,
                source_file_path=str(saved_path),
                source_filename=filename,
                processing_time_ms=processing_time_ms,
            )
            saved = self._repository.create(invoice)
        except AppError as exc:
            if saved_path is not None:
                saved_path.unlink(missing_ok=True)
            logger.warning("Failed to process invoice %s: %s", filename, exc.detail)
            return InvoiceUploadResult(filename=filename, status="failed", error=exc.detail)

        logger.info("Processed invoice %s -> %s", filename, saved.id)
        return InvoiceUploadResult(filename=filename, status="completed", invoice=saved)

    def _build_invoice(
        self,
        extracted: ExtractedInvoiceData,
        raw_text: str,
        source_file_path: str,
        source_filename: str,
        processing_time_ms: int,
    ) -> Invoice:
        payment_status = (
            extracted.payment_status
            if extracted.payment_status in _VALID_PAYMENT_STATUSES
            else PaymentStatus.UNKNOWN.value
        )

        return Invoice(
            vendor_name=extracted.vendor_name,
            vendor_email=extracted.vendor_email,
            invoice_number=extracted.invoice_number,
            invoice_date=extracted.invoice_date,
            material_type=extracted.material_type,
            subtotal_amount=extracted.subtotal_amount,
            tax_amount=extracted.tax_amount,
            total_amount=extracted.total_amount,
            currency=extracted.currency,
            payment_status=payment_status,
            raw_text=raw_text,
            structured_json=extracted.model_dump(mode="json"),
            source_file_path=source_file_path,
            source_filename=source_filename,
            llm_model=settings.GEMINI_MODEL,
            processed_at=datetime.now(timezone.utc),
            processing_time_ms=processing_time_ms,
            items=[
                InvoiceItem(
                    description=item.description,
                    material_type=item.material_type,
                    quantity=item.quantity,
                    unit=item.unit,
                    unit_price=item.unit_price,
                    line_total=item.line_total,
                )
                for item in extracted.items
            ],
        )
