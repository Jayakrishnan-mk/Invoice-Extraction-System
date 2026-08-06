import json
from unittest.mock import MagicMock

import pytest

from app.core.exceptions import AIExtractionError
from app.services.ai_extraction_service import AIExtractionService

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
        },
        {
            "description": "PPC Cement",
            "quantity": "100",
            "unit": "Bags",
            "unit_price": "390.00",
            "line_total": "39000.00",
        },
    ],
    "subtotal_amount": "144000.00",
    "tax_amount": "25920.00",
    "total_amount": "169920.00",
    "currency": "INR",
    "payment_status": "unpaid",
}


def _mock_client(response_text: str | None) -> MagicMock:
    client = MagicMock()
    client.models.generate_content.return_value = MagicMock(text=response_text)
    return client


@pytest.fixture
def service_with_client():
    client = _mock_client(json.dumps(VALID_PAYLOAD))
    return AIExtractionService(client=client), client


class TestExtract:
    def test_returns_validated_data_on_success(self, service_with_client):
        service, _client = service_with_client

        result = service.extract("raw invoice text")

        assert result.vendor_name == "ABC Cement Pvt Ltd"
        assert result.invoice_number == "INV-CEM-1001"
        assert len(result.items) == 2
        assert result.items[0].line_total == 105000
        assert result.total_amount == 169920

    def test_sends_raw_text_and_structured_output_config(self, service_with_client):
        service, client = service_with_client

        service.extract("raw invoice text")

        _args, kwargs = client.models.generate_content.call_args
        assert kwargs["contents"] == "raw invoice text"
        config = kwargs["config"]
        assert config.response_mime_type == "application/json"
        assert config.response_schema is not None

    def test_raises_when_gemini_call_fails(self):
        client = MagicMock()
        client.models.generate_content.side_effect = Exception("network error")
        service = AIExtractionService(client=client)

        with pytest.raises(AIExtractionError):
            service.extract("raw invoice text")

    def test_raises_when_response_is_empty(self):
        service = AIExtractionService(client=_mock_client(None))

        with pytest.raises(AIExtractionError):
            service.extract("raw invoice text")

    def test_raises_when_response_is_not_valid_json(self):
        service = AIExtractionService(client=_mock_client("not json"))

        with pytest.raises(AIExtractionError):
            service.extract("raw invoice text")

    def test_raises_when_response_is_missing_required_fields(self):
        incomplete = {"vendor_name": "ABC Cement Pvt Ltd"}
        service = AIExtractionService(client=_mock_client(json.dumps(incomplete)))

        with pytest.raises(AIExtractionError):
            service.extract("raw invoice text")
