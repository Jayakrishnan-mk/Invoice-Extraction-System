import uuid
from datetime import date, datetime, timezone
from decimal import Decimal

import pytest

from app.models.invoice import Invoice, PaymentStatus
from app.models.invoice_item import InvoiceItem


def make_invoice(
    db_session,
    *,
    vendor_name="ABC Cement Pvt Ltd",
    invoice_number="INV-CEM-1001",
    invoice_date=date(2026, 7, 1),
    material_type="Cement",
    total_amount=Decimal("123900.00"),
    payment_status=PaymentStatus.UNPAID.value,
    raw_text="sample raw invoice text",
    created_at=None,
) -> Invoice:
    invoice = Invoice(
        vendor_name=vendor_name,
        vendor_email=None,
        invoice_number=invoice_number,
        invoice_date=invoice_date,
        material_type=material_type,
        subtotal_amount=total_amount,
        tax_amount=Decimal("0.00"),
        total_amount=total_amount,
        payment_status=payment_status,
        raw_text=raw_text,
        structured_json={"vendor_name": vendor_name},
        source_file_path=f"/uploads/{invoice_number}.pdf",
        source_filename=f"{invoice_number}.pdf",
        llm_model="gemini-2.5-flash",
        processed_at=datetime.now(timezone.utc),
        processing_time_ms=120,
        **({"created_at": created_at} if created_at is not None else {}),
        items=[
            InvoiceItem(
                description="OPC 53 Grade Cement",
                material_type=material_type,
                quantity=Decimal("250"),
                unit="Bags",
                unit_price=Decimal("420.00"),
                line_total=total_amount,
            )
        ],
    )
    db_session.add(invoice)
    db_session.commit()
    db_session.refresh(invoice)
    return invoice


class TestListInvoices:
    def test_list_returns_all_invoices_newest_first(self, client, db_session):
        make_invoice(
            db_session, invoice_number="INV-1", created_at=datetime(2026, 1, 1, tzinfo=timezone.utc)
        )
        make_invoice(
            db_session, invoice_number="INV-2", created_at=datetime(2026, 1, 2, tzinfo=timezone.utc)
        )

        response = client.get("/api/v1/invoices")

        assert response.status_code == 200
        body = response.json()
        assert body["total"] == 2
        assert body["page"] == 1
        assert body["page_size"] == 20
        assert body["total_pages"] == 1
        assert [item["invoice_number"] for item in body["items"]] == ["INV-2", "INV-1"]
        assert "items" not in body["items"][0]  # summary shape, no line items key

    def test_list_filters_by_vendor_partial_match_case_insensitive(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", vendor_name="ABC Cement Pvt Ltd")
        make_invoice(db_session, invoice_number="INV-2", vendor_name="Steel Traders Co")

        response = client.get("/api/v1/invoices", params={"vendor": "cement"})

        assert response.status_code == 200
        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-1"

    def test_list_filters_by_material_type(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", material_type="Cement")
        make_invoice(db_session, invoice_number="INV-2", material_type="Steel")

        response = client.get("/api/v1/invoices", params={"material_type": "Steel"})

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-2"

    def test_list_filters_by_payment_status(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", payment_status=PaymentStatus.PAID.value)
        make_invoice(db_session, invoice_number="INV-2", payment_status=PaymentStatus.UNPAID.value)

        response = client.get("/api/v1/invoices", params={"payment_status": "paid"})

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-1"

    def test_list_filters_by_date_range(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", invoice_date=date(2026, 1, 15))
        make_invoice(db_session, invoice_number="INV-2", invoice_date=date(2026, 6, 15))

        response = client.get(
            "/api/v1/invoices",
            params={"date_from": "2026-05-01", "date_to": "2026-07-01"},
        )

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-2"

    def test_list_filters_by_amount_range(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", total_amount=Decimal("50000.00"))
        make_invoice(db_session, invoice_number="INV-2", total_amount=Decimal("150000.00"))

        response = client.get("/api/v1/invoices", params={"min_amount": "100000"})

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-2"

    def test_list_search_matches_invoice_number(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-CEM-1001")
        make_invoice(db_session, invoice_number="INV-STL-2002")

        response = client.get("/api/v1/invoices", params={"search": "STL"})

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-STL-2002"

    def test_list_search_matches_raw_text(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", raw_text="delivery note reference XYZ99")
        make_invoice(db_session, invoice_number="INV-2", raw_text="unrelated text")

        response = client.get("/api/v1/invoices", params={"search": "XYZ99"})

        items = response.json()["items"]
        assert len(items) == 1
        assert items[0]["invoice_number"] == "INV-1"

    def test_list_paginates(self, client, db_session):
        for i in range(5):
            make_invoice(db_session, invoice_number=f"INV-{i}")

        response = client.get("/api/v1/invoices", params={"page": 2, "page_size": 2})

        body = response.json()
        assert body["total"] == 5
        assert body["page"] == 2
        assert body["page_size"] == 2
        assert body["total_pages"] == 3
        assert len(body["items"]) == 2

    def test_list_rejects_inverted_date_range(self, client):
        response = client.get(
            "/api/v1/invoices",
            params={"date_from": "2026-07-01", "date_to": "2026-01-01"},
        )

        assert response.status_code == 422

    def test_list_rejects_inverted_amount_range(self, client):
        response = client.get(
            "/api/v1/invoices",
            params={"min_amount": "200000", "max_amount": "100000"},
        )

        assert response.status_code == 422

    def test_list_empty_when_no_invoices(self, client):
        response = client.get("/api/v1/invoices")

        assert response.status_code == 200
        body = response.json()
        assert body == {"items": [], "total": 0, "page": 1, "page_size": 20, "total_pages": 0}


class TestGetInvoiceDetail:
    def test_get_invoice_returns_full_detail(self, client, db_session):
        invoice = make_invoice(db_session, raw_text="full raw invoice body")

        response = client.get(f"/api/v1/invoices/{invoice.id}")

        assert response.status_code == 200
        body = response.json()
        assert body["id"] == str(invoice.id)
        assert body["raw_text"] == "full raw invoice body"
        assert body["structured_json"] == {"vendor_name": "ABC Cement Pvt Ltd"}
        assert body["source_file_path"] == invoice.source_file_path
        assert len(body["items"]) == 1
        assert body["items"][0]["description"] == "OPC 53 Grade Cement"

    def test_get_invoice_returns_404_when_missing(self, client):
        response = client.get(f"/api/v1/invoices/{uuid.uuid4()}")

        assert response.status_code == 404

    def test_get_invoice_returns_422_for_invalid_uuid(self, client):
        response = client.get("/api/v1/invoices/not-a-uuid")

        assert response.status_code == 422


class TestVendorsAndMaterials:
    def test_vendors_returns_distinct_sorted_names(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", vendor_name="Steel Traders Co")
        make_invoice(db_session, invoice_number="INV-2", vendor_name="ABC Cement Pvt Ltd")
        make_invoice(db_session, invoice_number="INV-3", vendor_name="ABC Cement Pvt Ltd")

        response = client.get("/api/v1/invoices/vendors")

        assert response.status_code == 200
        assert response.json() == ["ABC Cement Pvt Ltd", "Steel Traders Co"]

    def test_materials_returns_distinct_sorted_types(self, client, db_session):
        make_invoice(db_session, invoice_number="INV-1", material_type="Steel")
        make_invoice(db_session, invoice_number="INV-2", material_type="Cement")

        response = client.get("/api/v1/invoices/materials")

        assert response.status_code == 200
        assert response.json() == ["Cement", "Steel"]
