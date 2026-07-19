"""Pydantic schemas for issuers, signatures, numbering, rates, and settings."""
from datetime import date
from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class LoginIn(BaseModel):
    username: str
    password: str


class TokenOut(BaseModel):
    access_token: str
    token_type: str = "bearer"
    full_name: str | None = None


class IssuerIn(BaseModel):
    name: str
    address: str | None = None
    bin: str | None = None
    officer_name: str | None = None
    officer_designation: str | None = None
    officer_email: str | None = None
    default_bank_name: str | None = None
    default_description: str | None = None


class IssuerOut(ORM):
    id: int
    name: str
    address: str | None = None
    bin: str | None = None
    is_default: bool
    officer_name: str | None = None
    officer_designation: str | None = None
    officer_email: str | None = None
    default_bank_name: str | None = None
    default_description: str | None = None


class SignatureIn(BaseModel):
    name: str
    designation: str | None = None
    email: str | None = None
    enabled: bool = True


class SignatureOut(ORM):
    id: int
    name: str
    designation: str | None = None
    email: str | None = None
    enabled: bool


class NumberingIn(BaseModel):
    company_token: str
    fiscal_year_format: str = "YYYY-YY"
    separator: str = "/"
    pad_width: int = 3
    start_number: int = 1
    reset_policy: str = "per_fiscal_year"
    number_format: str = "{CompanyName}{sep}{FiscalYear}{sep}{AutoNumber}"


class NumberingOut(NumberingIn, ORM):
    id: int
    issuer_id: int


class RateIn(BaseModel):
    category_code: str
    description: str
    vds_rate: float
    base_rule: str = "deduct"
    effective_from: date | None = None


class RateOut(ORM):
    id: int
    category_code: str
    description: str
    vds_rate: float
    base_rule: str
    effective_from: date
    effective_to: date | None = None


class OrgSettingsIn(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_from: str | None = None
    smtp_use_tls: bool = True
    wa_provider: str = "cloud"
    wa_token: str | None = None
    wa_phone_number_id: str | None = None
    wa_twilio_sid: str | None = None
    wa_twilio_auth: str | None = None
    wa_twilio_from: str | None = None
    dispatch_mode: str = "online"
