"""Import batches, row errors, and invoice/transaction deduction lines.

value_excl / value_incl are database-GENERATED columns (see vds_database.sql),
so they are marked FetchedValue and never written by the ORM.
"""
from datetime import date, datetime
from sqlalchemy import (Date, DateTime, FetchedValue, ForeignKey, Integer, Numeric,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class ImportBatch(Base):
    __tablename__ = "import_batches"
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), index=True)
    file_name: Mapped[str] = mapped_column(String(300))
    total_rows: Mapped[int] = mapped_column(Integer, default=0)
    valid_rows: Mapped[int] = mapped_column(Integer, default=0)
    rejected_rows: Mapped[int] = mapped_column(Integer, default=0)
    status: Mapped[str] = mapped_column(String(20), default="pending")
    uploaded_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    uploaded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    errors: Mapped[list["ImportRowError"]] = relationship(
        back_populates="batch", cascade="all, delete-orphan")


class ImportRowError(Base):
    __tablename__ = "import_row_errors"
    id: Mapped[int] = mapped_column(primary_key=True)
    batch_id: Mapped[int] = mapped_column(ForeignKey("import_batches.id", ondelete="CASCADE"))
    row_number: Mapped[int] = mapped_column(Integer)
    column_name: Mapped[str | None] = mapped_column(String(64))
    message: Mapped[str] = mapped_column(Text)
    raw_row: Mapped[str | None] = mapped_column(Text)
    batch: Mapped[ImportBatch] = relationship(back_populates="errors")


class Invoice(Base):
    __tablename__ = "invoices"
    __table_args__ = (UniqueConstraint("issuer_id", "supplier_id", "invoice_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    import_batch_id: Mapped[int | None] = mapped_column(ForeignKey("import_batches.id"))
    invoice_no: Mapped[str | None] = mapped_column(String(60))
    invoice_date: Mapped[date | None] = mapped_column(Date)
    description: Mapped[str | None] = mapped_column(String(300))
    category_code: Mapped[str | None] = mapped_column(String(30))
    treasury_challan_no: Mapped[str | None] = mapped_column(String(60))
    treasury_deposit_date: Mapped[date | None] = mapped_column(Date)
    deducted_vat: Mapped[float] = mapped_column(Numeric(18, 2))
    vat_rate: Mapped[float] = mapped_column(Numeric(6, 4))
    # database-generated:
    value_excl: Mapped[float] = mapped_column(Numeric(18, 2), FetchedValue(), server_default=FetchedValue())
    value_incl: Mapped[float] = mapped_column(Numeric(18, 2), FetchedValue(), server_default=FetchedValue())
    deduction_date: Mapped[date] = mapped_column(Date)
    fiscal_year: Mapped[str] = mapped_column(String(9))
    status: Mapped[str] = mapped_column(String(20), default="staged")  # staged | certified
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    supplier = relationship("Supplier")
