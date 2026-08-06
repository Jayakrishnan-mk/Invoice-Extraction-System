"""Pydantic schema for AI-extracted invoice data.

Doubles as the contract Gemini's structured output must satisfy (mirrored by hand
into ``AIExtractionService._RESPONSE_SCHEMA`` in Gemini's own schema format - see
that module for why it isn't derived automatically via ``model_json_schema()``)
and as the validator applied to Gemini's response.
"""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class ExtractedInvoiceItem(BaseModel):
    description: str
    material_type: str | None = None
    quantity: Decimal
    unit: str
    unit_price: Decimal
    line_total: Decimal


class ExtractedInvoiceData(BaseModel):
    vendor_name: str
    vendor_email: str | None = None
    invoice_number: str
    invoice_date: date | None = None
    material_type: str
    items: list[ExtractedInvoiceItem]
    subtotal_amount: Decimal
    tax_amount: Decimal
    total_amount: Decimal
    currency: str = "INR"
    payment_status: str | None = None
