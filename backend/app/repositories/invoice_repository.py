import uuid

from sqlalchemy import or_
from sqlalchemy.orm import Session, selectinload

from app.models.invoice import Invoice
from app.schemas.invoice import InvoiceListParams


class InvoiceRepository:
    def __init__(self, db: Session):
        self.db = db

    def create(self, invoice: Invoice) -> Invoice:
        self.db.add(invoice)
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def get_by_id(self, invoice_id: uuid.UUID) -> Invoice | None:
        return (
            self.db.query(Invoice)
            .options(selectinload(Invoice.items))
            .filter(Invoice.id == invoice_id)
            .first()
        )

    def list_filtered(self, params: InvoiceListParams) -> tuple[list[Invoice], int]:
        query = self.db.query(Invoice)

        if params.vendor:
            query = query.filter(Invoice.vendor_name.ilike(f"%{params.vendor}%"))
        if params.material_type:
            query = query.filter(Invoice.material_type == params.material_type)
        if params.status:
            query = query.filter(Invoice.status == params.status)
        if params.payment_status:
            query = query.filter(Invoice.payment_status == params.payment_status)
        if params.date_from:
            query = query.filter(Invoice.invoice_date >= params.date_from)
        if params.date_to:
            query = query.filter(Invoice.invoice_date <= params.date_to)
        if params.min_amount is not None:
            query = query.filter(Invoice.total_amount >= params.min_amount)
        if params.max_amount is not None:
            query = query.filter(Invoice.total_amount <= params.max_amount)
        if params.search:
            pattern = f"%{params.search}%"
            query = query.filter(
                or_(
                    Invoice.vendor_name.ilike(pattern),
                    Invoice.invoice_number.ilike(pattern),
                    Invoice.raw_text.ilike(pattern),
                )
            )

        total = query.order_by(None).count()
        items = (
            query.order_by(Invoice.created_at.desc(), Invoice.id.desc())
            .offset((params.page - 1) * params.page_size)
            .limit(params.page_size)
            .all()
        )
        return items, total

    def list_distinct_vendors(self) -> list[str]:
        rows = self.db.query(Invoice.vendor_name).distinct().order_by(Invoice.vendor_name).all()
        return [row[0] for row in rows]

    def list_distinct_materials(self) -> list[str]:
        rows = self.db.query(Invoice.material_type).distinct().order_by(Invoice.material_type).all()
        return [row[0] for row in rows]

    def update(self, invoice: Invoice) -> Invoice:
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete(self, invoice: Invoice) -> None:
        self.db.delete(invoice)
        self.db.commit()
