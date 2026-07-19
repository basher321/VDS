"""Group staged invoices by supplier and issue one Mushak-6.6 certificate each."""
from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session

from ..models.certificate import Certificate, CertificateLine
from ..models.invoice import Invoice
from ..models.supplier import Supplier
from ..utils.formatting import round2, fiscal_year
from .serial_allocator import allocate_number
from .dedupe import already_certified


class GenerationError(Exception):
    pass


def pending_groups(db: Session, issuer_id: int) -> list[dict]:
    """One group per supplier that still has staged invoice lines."""
    invs = (db.query(Invoice)
            .filter(Invoice.issuer_id == issuer_id, Invoice.status == "staged")
            .all())
    groups: dict[int, dict] = {}
    for inv in invs:
        g = groups.setdefault(inv.supplier_id, {
            "supplier_id": inv.supplier_id,
            "supplier": inv.supplier.name,
            "bin": inv.supplier.bin,
            "period": inv.fiscal_year,
            "lines": [],
        })
        g["lines"].append(inv)
    out = []
    for g in groups.values():
        total_incl = sum(Decimal(str(i.value_incl)) for i in g["lines"])
        total_vat = sum(Decimal(str(i.deducted_vat)) for i in g["lines"])
        out.append({**g, "line_count": len(g["lines"]),
                    "total_incl": float(round2(total_incl)),
                    "total_vat": float(round2(total_vat))})
    return out


def generate_for_supplier(db: Session, issuer_id: int, supplier_id: int,
                          user_id: int | None = None) -> Certificate:
    invs = (db.query(Invoice)
            .filter(Invoice.issuer_id == issuer_id, Invoice.supplier_id == supplier_id,
                    Invoice.status == "staged")
            .order_by(Invoice.id).all())
    if not invs:
        raise GenerationError("No staged invoices for this supplier.")
    supplier = db.get(Supplier, supplier_id)
    period = invs[0].fiscal_year
    cert_no = allocate_number(db, issuer_id, period)

    total_incl = round2(sum(Decimal(str(i.value_incl)) for i in invs))
    total_vat = round2(sum(Decimal(str(i.deducted_vat)) for i in invs))

    cert = Certificate(
        issuer_id=issuer_id, supplier_id=supplier_id, certificate_no=cert_no,
        issue_date=date.today(), issue_date_mode="auto", fiscal_year=period,
        total_value_incl=total_incl, total_vat=total_vat, total_withheld=total_vat,
        has_bin=bool(supplier.bin and supplier.bin.strip()),
        status="generated", created_by=user_id,
    )
    db.add(cert)
    db.flush()

    for i, inv in enumerate(invs, start=1):
        if already_certified(db, inv.id):
            raise GenerationError(f"Invoice {inv.id} is already on a certificate.")
        db.add(CertificateLine(certificate_id=cert.id, invoice_id=inv.id, sl_no=i,
                               value_incl=inv.value_incl, vat_amount=inv.deducted_vat,
                               withheld_amount=inv.deducted_vat))
        inv.status = "certified"
    db.flush()
    return cert
