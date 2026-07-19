"""Settings: issuers, signatures, numbering, VDS rate master, global settings, uploads."""
import os
from datetime import date
from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.organization import Issuer, IssuerSignature, NumberingConfig, OrgSettings
from ..models.rate import VdsRate
from ..schemas.organization import (IssuerIn, IssuerOut, SignatureIn, SignatureOut,
                                    NumberingIn, NumberingOut, RateIn, RateOut, OrgSettingsIn)
from ..services import storage
from ..services.serial_allocator import get_numbering

router = APIRouter(prefix="/api", tags=["settings"])


# ---- issuers ----
@router.get("/issuers", response_model=list[IssuerOut])
def list_issuers(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(Issuer).order_by(Issuer.id).all()


@router.post("/issuers", response_model=IssuerOut)
def create_issuer(body: IssuerIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    issuer = Issuer(**body.model_dump())
    db.add(issuer)
    db.flush()
    db.add(NumberingConfig(issuer_id=issuer.id, company_token=issuer.name))
    db.commit()
    db.refresh(issuer)
    return issuer


@router.put("/issuers/{issuer_id}", response_model=IssuerOut)
def update_issuer(issuer_id: int, body: IssuerIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    issuer = db.get(Issuer, issuer_id) or _404()
    for k, v in body.model_dump().items():
        setattr(issuer, k, v)
    db.commit()
    db.refresh(issuer)
    return issuer


# ---- signatures ----
@router.get("/issuers/{issuer_id}/signatures", response_model=list[SignatureOut])
def list_signatures(issuer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(IssuerSignature).filter(IssuerSignature.issuer_id == issuer_id).all()


@router.post("/issuers/{issuer_id}/signatures", response_model=SignatureOut)
def add_signature(issuer_id: int, body: SignatureIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    sig = IssuerSignature(issuer_id=issuer_id, **body.model_dump())
    db.add(sig); db.commit(); db.refresh(sig)
    return sig


@router.put("/signatures/{sig_id}", response_model=SignatureOut)
def update_signature(sig_id: int, body: SignatureIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    sig = db.get(IssuerSignature, sig_id) or _404()
    for k, v in body.model_dump().items():
        setattr(sig, k, v)
    db.commit(); db.refresh(sig)
    return sig


@router.delete("/signatures/{sig_id}")
def delete_signature(sig_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    sig = db.get(IssuerSignature, sig_id) or _404()
    db.delete(sig); db.commit()
    return {"ok": True}


# ---- numbering ----
@router.get("/issuers/{issuer_id}/numbering", response_model=NumberingOut)
def read_numbering(issuer_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    return get_numbering(db, issuer_id)


@router.put("/issuers/{issuer_id}/numbering", response_model=NumberingOut)
def update_numbering(issuer_id: int, body: NumberingIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    cfg = get_numbering(db, issuer_id)
    for k, v in body.model_dump().items():
        setattr(cfg, k, v)
    db.commit(); db.refresh(cfg)
    return cfg


# ---- VDS rate master ----
@router.get("/rates", response_model=list[RateOut])
def list_rates(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.query(VdsRate).order_by(VdsRate.description).all()


@router.post("/rates", response_model=RateOut)
def add_rate(body: RateIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    data = body.model_dump()
    data["effective_from"] = data.get("effective_from") or date(2023, 7, 1)
    rate = VdsRate(**data)
    db.add(rate); db.commit(); db.refresh(rate)
    return rate


@router.put("/rates/{rate_id}", response_model=RateOut)
def update_rate(rate_id: int, body: RateIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rate = db.get(VdsRate, rate_id) or _404()
    data = body.model_dump()
    data["effective_from"] = data.get("effective_from") or rate.effective_from
    for k, v in data.items():
        setattr(rate, k, v)
    db.commit(); db.refresh(rate)
    return rate


@router.delete("/rates/{rate_id}")
def delete_rate(rate_id: int, db: Session = Depends(get_db), _=Depends(get_current_user)):
    rate = db.get(VdsRate, rate_id) or _404()
    db.delete(rate); db.commit()
    return {"ok": True}


# ---- global org settings (SMTP / WhatsApp / dispatch) ----
def _get_org(db: Session) -> OrgSettings:
    org = db.get(OrgSettings, 1)
    if not org:
        org = OrgSettings(id=1)
        db.add(org); db.flush()
    return org


@router.get("/org-settings")
def read_org(db: Session = Depends(get_db), _=Depends(get_current_user)):
    org = _get_org(db)
    return {c.name: getattr(org, c.name) for c in org.__table__.columns
            if c.name not in ("smtp_password", "wa_token", "wa_twilio_auth")}


@router.put("/org-settings")
def update_org(body: OrgSettingsIn, db: Session = Depends(get_db), _=Depends(get_current_user)):
    org = _get_org(db)
    for k, v in body.model_dump().items():
        if k in ("smtp_password", "wa_token", "wa_twilio_auth") and not v:
            continue  # keep stored secret
        setattr(org, k, v)
    db.commit()
    return {"ok": True}


# ---- image uploads (seal / letterhead / signature) ----
@router.post("/issuers/{issuer_id}/upload/{kind}")
def upload_image(issuer_id: int, kind: str, file: UploadFile = File(...),
                 db: Session = Depends(get_db), _=Depends(get_current_user)):
    if kind not in ("seal", "header", "footer"):
        raise HTTPException(400, "kind must be seal|header|footer")
    issuer = db.get(Issuer, issuer_id) or _404()
    ext = os.path.splitext(file.filename or "")[1] or ".png"
    path = storage.save("images", f"issuer{issuer_id}_{kind}{ext}", file.file.read())
    field = {"seal": "seal_path", "header": "letterhead_header_path", "footer": "letterhead_footer_path"}[kind]
    setattr(issuer, field, path)
    db.commit()
    return {"path": path}


@router.post("/signatures/{sig_id}/upload")
def upload_signature_image(sig_id: int, file: UploadFile = File(...),
                           db: Session = Depends(get_db), _=Depends(get_current_user)):
    sig = db.get(IssuerSignature, sig_id) or _404()
    ext = os.path.splitext(file.filename or "")[1] or ".png"
    sig.image_path = storage.save("images", f"signature{sig_id}{ext}", file.file.read())
    db.commit()
    return {"path": sig.image_path}


def _404():
    raise HTTPException(404, "Not found")
