"""Resolve the applicable VDS rate for a service category on a given date."""
from datetime import date
from sqlalchemy import and_, or_
from sqlalchemy.orm import Session
from ..models.rate import VdsRate


def resolve_rate(db: Session, category: str, on: date | None = None) -> float | None:
    on = on or date.today()
    q = (db.query(VdsRate)
         .filter(VdsRate.description == category,
                 VdsRate.effective_from <= on,
                 or_(VdsRate.effective_to.is_(None), VdsRate.effective_to >= on))
         .order_by(VdsRate.effective_from.desc()))
    row = q.first()
    return float(row.vds_rate) if row else None
