import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict


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
