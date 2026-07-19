"""Schemas for the import result surfaced to the UI."""
from pydantic import BaseModel


class ImportRowOut(BaseModel):
    excel_row: int
    supplier_name: str
    supplier_bin: str
    treasury_challan_no: str
    category: str
    deducted_vat: float | None = None
    vat_rate: float | None = None
    value_excl: float | None = None
    value_incl: float | None = None
    error: str | None = None


class ImportResultOut(BaseModel):
    batch_id: int
    filename: str
    total_rows: int
    ok_rows: int
    error_rows: int
    rows: list[ImportRowOut]
