import enum
import uuid
from datetime import date, datetime
from decimal import Decimal
from typing import TYPE_CHECKING

from sqlalchemy import Date, DateTime, Index, Integer, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database import Base

if TYPE_CHECKING:
    from app.models.invoice_item import InvoiceItem


class InvoiceStatus(str, enum.Enum):
    COMPLETED = "completed"


class PaymentStatus(str, enum.Enum):
    UNPAID = "unpaid"
    PAID = "paid"
    UNKNOWN = "unknown"


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (
        Index("ix_invoices_structured_json", "structured_json", postgresql_using="gin"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, server_default=text("gen_random_uuid()")
    )

    vendor_name: Mapped[str] = mapped_column(String(255), index=True)
    vendor_email: Mapped[str | None] = mapped_column(String(255))
    invoice_number: Mapped[str] = mapped_column(String(100), index=True)
    invoice_date: Mapped[date | None] = mapped_column(Date, index=True)
    material_type: Mapped[str] = mapped_column(String(100), index=True)

    subtotal_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    tax_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    total_amount: Mapped[Decimal] = mapped_column(Numeric(14, 2), index=True)
    currency: Mapped[str] = mapped_column(String(8), server_default="INR")

    # Plain VARCHAR rather than a native Postgres ENUM: lets a future async flow add
    # processing/failed status values without an ALTER TYPE migration. See CLAUDE.md
    # "Deliberate simplifications" - only "completed" is ever written today.
    status: Mapped[str] = mapped_column(
        String(20), server_default=InvoiceStatus.COMPLETED.value, index=True
    )
    payment_status: Mapped[str] = mapped_column(
        String(20), server_default=PaymentStatus.UNKNOWN.value
    )

    raw_text: Mapped[str] = mapped_column(Text)
    structured_json: Mapped[dict] = mapped_column(JSONB)

    source_file_path: Mapped[str] = mapped_column(String(500))
    source_filename: Mapped[str] = mapped_column(String(255))

    llm_model: Mapped[str] = mapped_column(String(100))
    processed_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    processing_time_ms: Mapped[int | None] = mapped_column(Integer)

    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )

    items: Mapped[list["InvoiceItem"]] = relationship(
        back_populates="invoice", cascade="all, delete-orphan", passive_deletes=True
    )
