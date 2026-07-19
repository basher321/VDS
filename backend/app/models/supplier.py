"""Suppliers and their email / WhatsApp contacts."""
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column, relationship
from ..core.database import Base


class Supplier(Base):
    __tablename__ = "suppliers"
    __table_args__ = (UniqueConstraint("issuer_id", "name", "bin"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    bin: Mapped[str | None] = mapped_column(String(20))
    address: Mapped[str | None] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    contacts: Mapped[list["SupplierContact"]] = relationship(
        back_populates="supplier", cascade="all, delete-orphan")


class SupplierContact(Base):
    __tablename__ = "supplier_contacts"
    __table_args__ = (UniqueConstraint("supplier_id", "kind", "value"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    supplier_id: Mapped[int] = mapped_column(ForeignKey("suppliers.id", ondelete="CASCADE"))
    kind: Mapped[str] = mapped_column(String(12))  # email | whatsapp
    value: Mapped[str] = mapped_column(String(255))
    is_primary: Mapped[bool] = mapped_column(Boolean, default=False)
    supplier: Mapped[Supplier] = relationship(back_populates="contacts")
