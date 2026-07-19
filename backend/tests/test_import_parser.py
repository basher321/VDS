import openpyxl
from app.services.import_parser import parse_summary


def test_parse_minimal_summary(tmp_path):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Summary"
    ws.append(["SL", "Supplier's Name", "Supplier's BIN", "Deducted VAT", "VAT Rate", "Notes"])
    ws.append([1, "Mohammad Ali", "", 30000, 0.15, "Consultant Fee"])
    p = tmp_path / "s.xlsx"
    wb.save(p)
    rows = parse_summary(str(p))
    assert len(rows) == 1
    assert rows[0]["supplier_name"] == "Mohammad Ali"
    assert rows[0]["deducted_vat"] == 30000
    assert abs(rows[0]["vat_rate"] - 0.15) < 1e-9
