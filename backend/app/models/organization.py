"""Users, issuers (withholding entities), signatures, numbering, global settings."""
from datetime import datetime

from sqlalchemy import (Boolean, DateTime, ForeignKey, Integer, Numeric, SmallInteger,
                        String, Text, UniqueConstraint, func)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from ..core.database import Base


class User(Base):
    __tablename__ = "users"
    id: Mapped[int] = mapped_column(primary_key=True)
    username: Mapped[str] = mapped_column(String(60), unique=True)
    email: Mapped[str | None] = mapped_column(String(120))
    password_hash: Mapped[str] = mapped_column(String(255))
    full_name: Mapped[str | None] = mapped_column(String(120))
    role: Mapped[str] = mapped_column(String(20), default="user")
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Issuer(Base):
    """A withholding entity that issues Mushak-6.6 certificates."""
    __tablename__ = "issuers"
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(200), unique=True)
    address: Mapped[str | None] = mapped_column(String(400))
    bin: Mapped[str | None] = mapped_column(String(20))
    is_default: Mapped[bool] = mapped_column(Boolean, default=False)
    officer_name: Mapped[str | None] = mapped_column(String(150))
    officer_designation: Mapped[str | None] = mapped_column(String(150))
    officer_email: Mapped[str | None] = mapped_column(String(150))
    default_bank_name: Mapped[str | None] = mapped_column(String(150))
    default_description: Mapped[str | None] = mapped_column(String(200), default="Supply of goods/services")
    seal_path: Mapped[str | None] = mapped_column(String(400))
    letterhead_header_path: Mapped[str | None] = mapped_column(String(400))
    letterhead_footer_path: Mapped[str | None] = mapped_column(String(400))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    signatures: Mapped[list["IssuerSignature"]] = relationship(
        back_populates="issuer", cascade="all, delete-orphan")
    numbering: Mapped["NumberingConfig"] = relationship(
        back_populates="issuer", cascade="all, delete-orphan", uselist=False)


class IssuerSignature(Base):
    __tablename__ = "issuer_signatures"
    __table_args__ = (UniqueConstraint("issuer_id", "name"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), index=True)
    name: Mapped[str] = mapped_column(String(150))
    designation: Mapped[str | None] = mapped_column(String(150))
    email: Mapped[str | None] = mapped_column(String(150))
    image_path: Mapped[str | None] = mapped_column(String(400))
    enabled: Mapped[bool] = mapped_column(Boolean, default=True)
    issuer: Mapped[Issuer] = relationship(back_populates="signatures")


class NumberingConfig(Base):
    __tablename__ = "numbering_config"
    id: Mapped[int] = mapped_column(primary_key=True)
    issuer_id: Mapped[int] = mapped_column(ForeignKey("issuers.id", ondelete="CASCADE"), unique=True)
    company_token: Mapped[str] = mapped_column(String(64), default="VDS")
    fiscal_year_format: Mapped[str] = mapped_column(String(16), default="YYYY-YY")
    separator: Mapped[str] = mapped_column(String(4), default="/")
    pad_width: Mapped[int] = mapped_column(Integer, default=3)
    start_number: Mapped[int] = mapped_column(Integer, default=1)
    reset_policy: Mapped[str] = mapped_column(String(16), default="per_fiscal_year")
    number_format: Mapped[str] = mapped_column(
        String(128), default="{CompanyName}{sep}{FiscalYear}{sep}{AutoNumber}")
    issuer: Mapped[Issuer] = relationship(back_populates="numbering")


class OrgSettings(Base):
    """Single global row (id=1): SMTP / WhatsApp / dispatch transport config."""
    __tablename__ = "org_settings"
    id: Mapped[int] = mapped_column(SmallInteger, primary_key=True, default=1)
    smtp_host: Mapped[str | None] = mapped_column(String(255))
    smtp_port: Mapped[int | None] = mapped_column(Integer, default=587)
    smtp_user: Mapped[str | None] = mapped_column(String(255))
    smtp_password: Mapped[str | None] = mapped_column(String(255))
    smtp_from: Mapped[str | None] = mapped_column(String(255))
    smtp_use_tls: Mapped[bool] = mapped_column(Boolean, default=True)
    wa_provider: Mapped[str] = mapped_column(String(20), default="cloud")
    wa_token: Mapped[str | None] = mapped_column(String(512))
    wa_phone_number_id: Mapped[str | None] = mapped_column(String(64))
    wa_twilio_sid: Mapped[str | None] = mapped_column(String(64))
    wa_twilio_auth: Mapped[str | None] = mapped_column(String(128))
    wa_twilio_from: Mapped[str | None] = mapped_column(String(32))
    dispatch_mode: Mapped[str] = mapped_column(String(10), default="online")
