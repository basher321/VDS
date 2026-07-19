"""Duplicate-line guard: an invoice may appear on only one live certificate."""
from sqlalchemy.orm import Session
from ..models.certificate import CertificateLine


def already_certified(db: Session, invoice_id: int) -> bool:
    return db.query(CertificateLine).filter(CertificateLine.invoice_id == invoice_id).first() is not None
