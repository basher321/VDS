"""Dashboard summary counts."""
from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.invoice import Invoice
from ..models.certificate import Certificate, DispatchJob
from ..models.supplier import Supplier

router = APIRouter(prefix="/api/dashboard", tags=["dashboard"])


@router.get("")
def summary(db: Session = Depends(get_db), _=Depends(get_current_user)):
    staged = db.query(func.count(Invoice.id)).filter(Invoice.status == "staged").scalar() or 0
    lines = db.query(func.count(Invoice.id)).scalar() or 0
    suppliers = db.query(func.count(Supplier.id)).scalar() or 0
    generated = db.query(func.count(Certificate.id)).filter(Certificate.status == "generated").scalar() or 0
    sent = db.query(func.count(Certificate.id)).filter(Certificate.status == "sent").scalar() or 0
    total_vat = db.query(func.coalesce(func.sum(Certificate.total_vat), 0)).scalar() or 0
    queue = db.query(func.count(DispatchJob.id)).filter(DispatchJob.status == "queued").scalar() or 0
    # pending supplier groups = distinct suppliers with staged invoices
    pending = (db.query(func.count(func.distinct(Invoice.supplier_id)))
               .filter(Invoice.status == "staged").scalar() or 0)
    return {
        "imported_lines": lines, "suppliers": suppliers,
        "pending_groups": pending, "queued_dispatches": queue,
        "total_vat_withheld": float(total_vat),
        "certificates": {"generated": generated, "sent": sent},
    }
