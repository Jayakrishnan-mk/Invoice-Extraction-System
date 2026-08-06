import math
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class InvoiceItemRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    description: str
    material_type: str | None
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal


class InvoiceRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_name: str
    vendor_email: str | None
    invoice_number: str
    invoice_date: date | None
    material_type: str
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str
    status: str
    payment_status: str
    source_filename: str
    llm_model: str
    processed_at: datetime
    processing_time_ms: int | None
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceItemRead]


class InvoiceUploadResult(BaseModel):
    filename: str
    status: Literal["completed", "failed"]
    invoice: InvoiceRead | None = None
    error: str | None = None


class InvoiceUploadResponse(BaseModel):
    results: list[InvoiceUploadResult]


class InvoiceDetail(InvoiceRead):
    """Full invoice detail: everything in InvoiceRead plus raw text and the full
    structured extraction result, for the invoice detail page."""

    source_file_path: str
    raw_text: str
    structured_json: dict


class InvoiceListItem(BaseModel):
    """Lightweight row for the invoice list page — no line items or raw text."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    vendor_name: str
    invoice_number: str
    invoice_date: date | None
    material_type: str
    total_amount: Decimal
    currency: str
    status: str
    payment_status: str
    source_filename: str
    created_at: datetime


class InvoiceListParams(BaseModel):
    """Query params for GET /invoices — filters, free-text search, and pagination."""

    vendor: str | None = Field(None, description="Filter by vendor name (partial match)")
    material_type: str | None = Field(None, description="Filter by material type (exact match)")
    status: str | None = Field(None, description="Filter by processing status")
    payment_status: str | None = Field(None, description="Filter by payment status")
    date_from: date | None = Field(None, description="Invoice date lower bound (inclusive)")
    date_to: date | None = Field(None, description="Invoice date upper bound (inclusive)")
    min_amount: Decimal | None = Field(None, ge=0, description="Minimum total amount")
    max_amount: Decimal | None = Field(None, ge=0, description="Maximum total amount")
    search: str | None = Field(
        None, description="Free text search over vendor name, invoice number, and raw text"
    )
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)

    @model_validator(mode="after")
    def _check_ranges(self) -> "InvoiceListParams":
        if self.date_from and self.date_to and self.date_from > self.date_to:
            raise ValueError("date_from must be on or before date_to")
        if self.min_amount is not None and self.max_amount is not None and self.min_amount > self.max_amount:
            raise ValueError("min_amount must be less than or equal to max_amount")
        return self


class InvoiceListResponse(BaseModel):
    items: list[InvoiceListItem]
    total: int
    page: int
    page_size: int
    total_pages: int

    @classmethod
    def build(cls, items: list[InvoiceListItem], total: int, page: int, page_size: int) -> "InvoiceListResponse":
        total_pages = math.ceil(total / page_size) if total else 0
        return cls(items=items, total=total, page=page, page_size=page_size, total_pages=total_pages)
