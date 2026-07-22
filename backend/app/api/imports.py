"""Import module: upload the Mushak-6.6 Summary workbook, validate, stage rows."""
import json
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy.orm import Session

from ..core.database import get_db
from ..core.security import get_current_user
from ..models.invoice import ImportBatch, ImportRowError, Invoice
from ..models.supplier import Supplier
from ..schemas.import_ import ImportResultOut, ImportRowOut
from ..services.import_parser import parse_summary
from ..services.validators import validate_import_row
from ..services.vds_calculator import derive
from ..utils.formatting import fiscal_year
from datetime import date

router = APIRouter(prefix="/api/import", tags=["import"])


@router.post("", response_model=ImportResultOut)
def upload(issuer_id: int = Form(...), file: UploadFile = File(...),
           db: Session = Depends(get_db), user=Depends(get_current_user)):
    if not (file.filename or "").lower().endswith(".xlsx"):
        raise HTTPException(400, "Only .xlsx workbooks are supported.")

    try:
        parsed = parse_summary(file.file.read())
    except Exception as e:
        raise HTTPException(400, f"Could not parse the workbook: {e}")

    batch = ImportBatch(issuer_id=issuer_id, file_name=file.filename, total_rows=len(parsed),
                        uploaded_by=user.id)
    db.add(batch)
    db.flush()

    seen_challans: set[str] = set()
    out_rows, ok, bad = [], 0, 0
    for row in parsed:
        err = validate_import_row(row)
        excl = incl = None
        if not err:
            try:
                d = derive(row["deducted_vat"], row["vat_rate"])
                excl, incl = float(d["value_excl"]), float(d["value_incl"])
            except ValueError as ve:
                err = str(ve)

        challan = row["treasury_challan_no"]
        if not err and challan:
            if challan in seen_challans or _challan_already_imported(db, issuer_id, challan):
                err = f"Treasury challan {challan} was already imported for this issuer."
            else:
                seen_challans.add(challan)

        if err:
            bad += 1
            db.add(ImportRowError(batch_id=batch.id, row_number=row["excel_row"],
                                  message=err, raw_row=json.dumps(row, default=str)))
        else:
            ok += 1
            supplier = _get_or_create_supplier(db, issuer_id, row)
            ddate = row["treasury_deposit_date"] or row["invoice_date"] or date.today()
            db.add(Invoice(
                issuer_id=issuer_id, supplier_id=supplier.id, import_batch_id=batch.id,
                invoice_no=row["invoice_no"] or None, invoice_date=row["invoice_date"],
                description=row["category"] or None, category_code=row["category"] or None,
                treasury_challan_no=row["treasury_challan_no"] or None,
                treasury_deposit_date=row["treasury_deposit_date"],
                deducted_vat=row["deducted_vat"], vat_rate=row["vat_rate"],
                deduction_date=ddate, fiscal_year=fiscal_year(ddate), status="staged"))

        out_rows.append(ImportRowOut(
            excel_row=row["excel_row"], supplier_name=row["supplier_name"],
            supplier_bin=row["supplier_bin"], treasury_challan_no=row["treasury_challan_no"],
            category=row["category"], deducted_vat=row["deducted_vat"], vat_rate=row["vat_rate"],
            value_excl=excl, value_incl=incl, error=err))

    batch.valid_rows, batch.rejected_rows, batch.status = ok, bad, "completed"
    db.commit()

    return ImportResultOut(batch_id=batch.id, filename=file.filename, total_rows=len(parsed),
                           ok_rows=ok, error_rows=bad, rows=out_rows)


def _challan_already_imported(db: Session, issuer_id: int, challan: str) -> bool:
    return (db.query(Invoice)
            .filter(Invoice.issuer_id == issuer_id, Invoice.treasury_challan_no == challan)
            .first() is not None)


def _get_or_create_supplier(db: Session, issuer_id: int, row: dict) -> Supplier:
    q = (db.query(Supplier)
         .filter(Supplier.issuer_id == issuer_id, Supplier.name == row["supplier_name"]))
    supplier = q.first()
    if supplier:
        if not supplier.bin and row["supplier_bin"]:
            supplier.bin = row["supplier_bin"]
        return supplier
    supplier = Supplier(issuer_id=issuer_id, name=row["supplier_name"],
                        bin=row["supplier_bin"] or None)
    db.add(supplier)
    db.flush()
    return supplier
