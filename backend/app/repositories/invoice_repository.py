import uuid

from sqlalchemy.orm import Session, selectinload

from app.models.invoice import Invoice


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

    def list_all(self, skip: int = 0, limit: int = 100) -> list[Invoice]:
        return (
            self.db.query(Invoice)
            .order_by(Invoice.created_at.desc())
            .offset(skip)
            .limit(limit)
            .all()
        )

    def update(self, invoice: Invoice) -> Invoice:
        self.db.commit()
        self.db.refresh(invoice)
        return invoice

    def delete(self, invoice: Invoice) -> None:
        self.db.delete(invoice)
        self.db.commit()
