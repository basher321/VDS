"""Field-level validation used by import and certificate generation."""
import re

BIN_RE = re.compile(r"^\d{9}-\d{4}$")
EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
WHATSAPP_RE = re.compile(r"^\+?\d{10,15}$")


def valid_issuer_bin(bin_: str | None) -> bool:
    return bool(bin_) and bool(BIN_RE.match(bin_))


def valid_email(v: str | None) -> bool:
    return bool(v) and bool(EMAIL_RE.match(v))


def valid_whatsapp(v: str | None) -> bool:
    return bool(v) and bool(WHATSAPP_RE.match(re.sub(r"[\s-]", "", v)))


def validate_import_row(row: dict) -> str | None:
    """Return an error message, or None if the row is valid."""
    try:
        vat = float(row.get("deducted_vat") or 0)
        rate = float(row.get("vat_rate") or 0)
    except (TypeError, ValueError):
        return "Deducted VAT and VAT rate must be numeric"
    if vat <= 0 or rate <= 0:
        return "VAT/rate must be greater than 0"
    if not row.get("supplier_name"):
        return "Supplier name is required"
    return None
