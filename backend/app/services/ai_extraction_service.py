import json
import logging

from google import genai
from google.genai import types
from pydantic import ValidationError

from app.config import settings
from app.core.exceptions import AIExtractionError
from app.schemas.extraction import ExtractedInvoiceData

logger = logging.getLogger(__name__)

_SYSTEM_INSTRUCTION = (
    "You are an expert at reading invoices issued by Indian construction-material "
    "vendors (cement, steel, bricks, sand, aggregates, and similar). Extract the "
    "invoice into the exact structured schema provided. Amounts are typically in "
    "Indian Rupees and may include GST. Transcribe every line item exactly as "
    "printed - do not summarize or merge rows. If a field is not present on the "
    "invoice, omit it rather than guessing. Represent every monetary and quantity "
    "value as a decimal string (e.g. '1234.50'), never as a rounded float."
)

# Built by hand rather than derived from ExtractedInvoiceData.model_json_schema():
# google-genai 0.3.0's response_schema conversion (t_schema/process_schema) does not
# resolve the $ref/$defs or anyOf that pydantic emits for nested models and
# Decimal/Optional fields, and raises a validation error on them. A hand-written
# schema in Gemini's OpenAPI subset sidesteps that entirely. Also note: the
# Gemini Developer API (api_key auth, no vertexai=True) rejects "nullable" outright
# (_Schema_to_mldev raises on it) - optional fields are just left out of "required"
# instead, which is enough since ExtractedInvoiceData gives them None defaults.
# Keep this in sync with ExtractedInvoiceData/ExtractedInvoiceItem.
_ITEM_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "description": {"type": "STRING"},
        "material_type": {"type": "STRING"},
        "quantity": {"type": "STRING", "description": "Decimal quantity as a string, e.g. '120.5'"},
        "unit": {"type": "STRING", "description": "Unit of measure, e.g. bags, tonnes, cu.m, sq.ft"},
        "unit_price": {"type": "STRING", "description": "Decimal unit price as a string"},
        "line_total": {"type": "STRING", "description": "Decimal line total as a string"},
    },
    "required": ["description", "quantity", "unit", "unit_price", "line_total"],
}

_RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "vendor_name": {"type": "STRING"},
        "vendor_email": {"type": "STRING"},
        "invoice_number": {"type": "STRING"},
        "invoice_date": {"type": "STRING", "description": "ISO 8601 date, YYYY-MM-DD"},
        "material_type": {
            "type": "STRING",
            "description": "Primary material category for this invoice, e.g. Cement, Steel, Bricks, Sand",
        },
        "items": {"type": "ARRAY", "items": _ITEM_SCHEMA},
        "subtotal_amount": {"type": "STRING", "description": "Decimal subtotal as a string"},
        "tax_amount": {"type": "STRING", "description": "Decimal tax amount as a string"},
        "total_amount": {"type": "STRING", "description": "Decimal total amount as a string"},
        "currency": {"type": "STRING", "description": "ISO currency code, e.g. INR"},
        "payment_status": {
            "type": "STRING",
            "description": "'paid' or 'unpaid' if explicitly stated on the invoice, otherwise omit this field",
        },
    },
    "required": [
        "vendor_name",
        "invoice_number",
        "material_type",
        "items",
        "subtotal_amount",
        "tax_amount",
        "total_amount",
        "currency",
    ],
}


class AIExtractionService:
    """Turns raw invoice text into structured data via Gemini structured output.

    Uses response_mime_type=application/json + a fixed response_schema so Gemini
    returns guaranteed-parseable JSON, then validates that JSON against
    ExtractedInvoiceData. Raises AIExtractionError on any API failure or schema
    mismatch - no partial results, no fallback parsing (see CLAUDE.md "Deliberate
    simplifications").
    """

    def __init__(self, client: genai.Client | None = None):
        self._client = client or genai.Client(api_key=settings.GEMINI_API_KEY)

    def extract(self, raw_text: str) -> ExtractedInvoiceData:
        try:
            response = self._client.models.generate_content(
                model=settings.GEMINI_MODEL,
                contents=raw_text,
                config=types.GenerateContentConfig(
                    system_instruction=_SYSTEM_INSTRUCTION,
                    response_mime_type="application/json",
                    response_schema=_RESPONSE_SCHEMA,
                    temperature=0.1,
                ),
            )
        except Exception as exc:
            logger.exception("Gemini request failed during invoice extraction")
            raise AIExtractionError("Failed to reach Gemini for invoice extraction") from exc

        if not response.text:
            logger.error("Gemini returned an empty extraction response")
            raise AIExtractionError("Gemini returned an empty extraction response")

        try:
            return ExtractedInvoiceData.model_validate_json(response.text)
        except (ValidationError, json.JSONDecodeError) as exc:
            logger.exception("Gemini response failed schema validation: %s", response.text)
            raise AIExtractionError("Gemini response did not match the expected invoice schema") from exc
