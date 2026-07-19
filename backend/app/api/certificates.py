"""Certificate Issue: pending groups, generate, list, preview edits, dispatch."""
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user, get_current_user_flexible
from ..models.certificate import Certificate, CertificateLine, DispatchJob
from ..models.invoice import Invoice
from ..models.organization import Issuer, OrgSettings
from ..models.supplier import Supplier, SupplierContact
from ..schemas.certificate import (PendingGroupOut, CertificateOut, GenerateIn, RemarksIn,
                                   BinStatusIn, IssueDateIn, DispatchIn)
from ..services import storage
from ..services.certificate_builder import pending_groups, generate_for_supplier, GenerationError
from ..services.pdf_renderer import render_certificate_pdf

router = APIRouter(prefix="/api/certificates", tags=["certificates"])


def _cert_out(c: Certificate) -> CertificateOut:
    return CertificateOut(
        id=c.id, certificate_no=c.certificate_no, supplier=c.supplier.name, bin=c.supplier.bin,
        period=c.fiscal_year, issue_date=c.issue_date, issue_date_mode=c.issue_date_mode,
        total_value_incl=float(c.total_value_incl), total_vat=float(c.total_vat),
        total_withheld=float(c.total_withheld), has_bin=c.has_bin, remarks=c.remarks, status=c.status)


def _render(db: Session, cert: Certificate) -> str:
    issuer = db.get(Issuer, cert.issuer_id)
    supplier = db.get(Supplier, cert.supplier_id)
    lines = []
    for ln in cert.lines:
        inv = ln.invoice
        lines.append({"challan": inv.treasury_challan_no or "", "cdate": inv.treasury_deposit_date,
                      "inv": inv.invoice_no or "", "idate": inv.invoice_date,
                      "value_incl": float(ln.value_incl), "vat": float(ln.vat_amount)})
    path = render_certificate_pdf(cert, issuer, supplier, lines)
    cert.pdf_path = path
    db.commit()
    return path


@router.get("/pending", response_model=list[PendingGroupOut])
def pending(issuer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return [PendingGroupOut(**g) for g in pending_groups(db, issuer_id)]


@router.get("", response_model=list[CertificateOut])
def list_certs(issuer_id: int, bin: str = "", supplier: str = "",
               db: Session = Depends(get_db), _=Depends(get_current_user)):
    q = db.query(Certificate).filter(Certificate.issuer_id == issuer_id)
    rows = q.order_by(Certificate.id.desc()).all()
    def keep(c):
        if bin and bin.lower() not in (c.supplier.bin or "").lower():
            return False
        if supplier and supplier.lower() not in c.supplier.name.lower():
            return False
        return True
    return [_cert_out(c) for c in rows if keep(c)]


@router.post("/generate", response_model=CertificateOut)
def generate(issuer_id: int, body: GenerateIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    try:
        cert = generate_for_supplier(db, issuer_id, body.supplier_id, user.id)
    except GenerationError as e:
        raise HTTPException(400, str(e))
    db.commit()
    _render(db, cert)
    db.refresh(cert)
    return _cert_out(cert)


@router.get("/{cert_id}", response_model=CertificateOut)
def get_cert(cert_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cert = db.get(Certificate, cert_id) or _404()
    return _cert_out(cert)


@router.get("/{cert_id}/pdf")
def get_pdf(cert_id: int, db: Session = Depends(get_db), _=Depends(get_current_user_flexible)):
    cert = db.get(Certificate, cert_id) or _404()
    data = storage.load(cert.pdf_path)
    if data is None:
        _render(db, cert)
        data = storage.load(cert.pdf_path)
    safe = cert.certificate_no.replace("/", "_").replace("\\", "_")
    return Response(content=data, media_type="application/pdf",
                    headers={"Content-Disposition": f'inline; filename="{safe}.pdf"'})


@router.put("/{cert_id}/remarks", response_model=CertificateOut)
def set_remarks(cert_id: int, body: RemarksIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cert = db.get(Certificate, cert_id) or _404()
    cert.remarks = body.remarks
    db.commit()
    _render(db, cert)
    return _cert_out(cert)


@router.put("/{cert_id}/bin-status", response_model=CertificateOut)
def set_bin(cert_id: int, body: BinStatusIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cert = db.get(Certificate, cert_id) or _404()
    cert.has_bin = body.has_bin
    db.commit()
    _render(db, cert)
    return _cert_out(cert)


@router.put("/{cert_id}/issue-date", response_model=CertificateOut)
def set_issue_date(cert_id: int, body: IssueDateIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    from datetime import date as _date
    cert = db.get(Certificate, cert_id) or _404()
    if body.mode == "manual":
        if not body.on_date:
            raise HTTPException(400, "Pick a date for Manual mode.")
        cert.issue_date = body.on_date
    else:
        cert.issue_date = _date.today()
    cert.issue_date_mode = body.mode
    db.commit()
    _render(db, cert)
    return _cert_out(cert)


@router.get("/{cert_id}/anomalies")
def anomalies(cert_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cert = db.get(Certificate, cert_id) or _404()
    out = []
    if not cert.has_bin:
        out.append({"code": "MISSING_BIN", "message": "Supplier BIN is not on record."})
    emails = [c.value for c in cert.supplier.contacts if c.kind == "email"]
    if not emails:
        out.append({"code": "NO_EMAIL", "message": "No email contact on record for this supplier."})
    return out


@router.post("/{cert_id}/dispatch")
def dispatch(cert_id: int, body: DispatchIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cert = db.get(Certificate, cert_id) or _404()
    anos = anomalies(cert_id, db)
    if anos and not body.override_reason:
        raise HTTPException(409, {"blocked": True, "anomalies": anos})
    if body.override_reason:
        cert.override_reason = body.override_reason

    org = db.get(OrgSettings, 1)
    contact_kind = "email" if body.channel == "email" else "whatsapp"
    recipients = [c.value for c in cert.supplier.contacts if c.kind == contact_kind]
    if not recipients:
        raise HTTPException(400, f"No {contact_kind} contact on record for this supplier.")

    jobs = []
    for rcpt in recipients:
        status = "queued" if (org and org.dispatch_mode == "offline") else "sent"
        job = DispatchJob(certificate_id=cert.id, channel=body.channel, recipient=rcpt, status=status,
                          sent_at=datetime.utcnow() if status == "sent" else None)
        db.add(job)
        jobs.append(job)
    if any(j.status == "sent" for j in jobs):
        cert.status = "sent"
    db.commit()
    return [{"recipient": j.recipient, "status": j.status} for j in jobs]


@router.get("/{cert_id}/dispatch-jobs")
def dispatch_jobs(cert_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    jobs = db.query(DispatchJob).filter(DispatchJob.certificate_id == cert_id).all()
    return [{"id": j.id, "channel": j.channel, "recipient": j.recipient, "status": j.status,
             "opened_at": j.opened_at.isoformat() if j.opened_at else None} for j in jobs]


def _404():
    raise HTTPException(404, "Certificate not found")
