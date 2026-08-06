from fastapi import Depends
from sqlalchemy.orm import Session

from app.database import get_db
from app.repositories.invoice_repository import InvoiceRepository
from app.services.ai_extraction_service import AIExtractionService
from app.services.invoice_service import InvoiceService
from app.services.pdf_service import PDFService

__all__ = ["get_db", "get_invoice_service"]


def get_pdf_service() -> PDFService:
    return PDFService()


def get_ai_extraction_service() -> AIExtractionService:
    return AIExtractionService()


def get_invoice_repository(db: Session = Depends(get_db)) -> InvoiceRepository:
    return InvoiceRepository(db)


def get_invoice_service(
    pdf_service: PDFService = Depends(get_pdf_service),
    ai_service: AIExtractionService = Depends(get_ai_extraction_service),
    repository: InvoiceRepository = Depends(get_invoice_repository),
) -> InvoiceService:
    return InvoiceService(pdf_service, ai_service, repository)
