"""Certificates, their printed lines, and dispatch jobs."""
from datetime import date, datetime
from sqlalchemy import (Boolean, Date, DateTime, ForeignKey, Integer, Numeric,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class Certificate(Base):
    __tablename__ = "certificates"
    __table_args__ = (UniqueConstraint("issuer_id", "certificate_no"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), index=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id"))
    certificate_no: Mapped[str] = mapped_column(String(64))
    issue_date: Mapped[date] = mapped_column(Date, default=date.today)
    issue_date_mode: Mapped[str] = mapped_column(String(10), default="auto")
    fiscal_year: Mapped[str] = mapped_column(String(9))
    total_value_incl: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_vat: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    total_withheld: Mapped[float] = mapped_column(Numeric(18, 2), default=0)
    has_bin: Mapped[bool] = mapped_column(Boolean, default=False)
    remarks: Mapped[str | None] = mapped_column(Text)
    override_reason: Mapped[str | None] = mapped_column(Text)
    status: Mapped[str] = mapped_column(String(20), default="generated")
    pdf_path: Mapped[str | None] = mapped_column(String(400))
    replaces_cert_id: Mapped[int | None] = mapped_column(ForeignKey("certificates.id"))
    created_by: Mapped[int | None] = mapped_column(ForeignKey("users.id"))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    issuer = relationship("Issuer")
    supplier = relationship("Supplier")
    lines: Mapped[list["CertificateLine"]] = relationship(
        back_populates="certificate", cascade="all, delete-orphan", order_by="CertificateLine.sl_no")


class CertificateLine(Base):
    __tablename__ = "certificate_lines"
    id: Mapped[int] = mapped_column(primary_key=True)
    certificate_id: Mapped[int] = mapped_column(ForeignKey("certificates.id", ondelete="CASCADE"))
    invoice_id: Mapped[int] = mapped_column(ForeignKey("invoices.id"), unique=True)
    sl_no: Mapped[int] = mapped_column(Integer)
    value_incl: Mapped[float] = mapped_column(Numeric(18, 2))
    vat_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    withheld_amount: Mapped[float] = mapped_column(Numeric(18, 2))
    certificate: Mapped[Certificate] = relationship(back_populates="lines")
    invoice = relationship("Invoice")


class DispatchJob(Base):
    __tablename__ = "dispatch_jobs"
    id: Mapped[int] = mapped_column(primary_key=True)
    certificate_id: Mapped[int] = mapped_column(ForeignKey("certificates.id", ondelete="CASCADE"), index=True)
    channel: Mapped[str] = mapped_column(String(12))  # email | whatsapp
    recipient: Mapped[str] = mapped_column(String(255))
    status: Mapped[str] = mapped_column(String(12), default="queued")
    attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_error: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    opened_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
