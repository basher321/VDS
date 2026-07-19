"""Schemas for pending groups, certificates, and dispatch."""
from datetime import date
from pydantic import BaseModel, ConfigDict


class ORM(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class PendingGroupOut(BaseModel):
    supplier_id: int
    supplier: str
    bin: str | None = None
    period: str
    line_count: int
    total_incl: float
    total_vat: float


class CertLineOut(BaseModel):
    sl_no: int
    challan: str | None = None
    cdate: str | None = None
    inv: str | None = None
    idate: str | None = None
    value_incl: float
    vat: float


class CertificateOut(ORM):
    id: int
    certificate_no: str
    supplier: str
    bin: str | None = None
    period: str
    issue_date: date
    issue_date_mode: str
    total_value_incl: float
    total_vat: float
    total_withheld: float
    has_bin: bool
    remarks: str | None = None
    status: str


class GenerateIn(BaseModel):
    supplier_id: int


class RemarksIn(BaseModel):
    remarks: str


class BinStatusIn(BaseModel):
    has_bin: bool


class IssueDateIn(BaseModel):
    mode: str                 # auto | manual
    on_date: date | None = None


class DispatchIn(BaseModel):
    channel: str = "email"   # email | whatsapp
    override_reason: str | None = None
