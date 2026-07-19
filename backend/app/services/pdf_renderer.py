"""Render a Certificate to a Mushak-6.6 PDF matching the XFL 'Cerificate' tab.

Layout: centred government header + 'Mushak-6.6' and issuer logo top-right;
issuer block; Certificate No / Date of Issue; Section-49 body; the bordered
deduction table (SL / Supplier Name+BIN / Treasury Challan No+Date / Concerned
tax invoice No+Date / Total Value of Supply* / Amount of VAT / Amount withheld)
with a treasury-narrative row and Total row; then a single left-aligned
Officer-in-Charge signature block; footnote. No seal, no multi-signature grid.
"""
import os
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image)

from ..core.config import get_settings
from ..utils.formatting import money

_LOGO = os.path.join(os.path.dirname(__file__), "..", "assets", "logo", "issuer_logo.png")


def _P(t, fs=8, al=TA_LEFT, bold=False, lead=None):
    fn = "Helvetica-Bold" if bold else "Helvetica"
    return Paragraph(str(t), ParagraphStyle("x", fontName=fn, fontSize=fs, alignment=al, leading=lead or fs + 2))


def render_certificate_pdf(cert, issuer, supplier, lines) -> str:
    """lines: list of dicts {challan, cdate, inv, idate, value_incl, vat}."""
    settings = get_settings()
    os.makedirs(settings.certificate_dir, exist_ok=True)
    safe = cert.certificate_no.replace("/", "_").replace("\\", "_")
    path = os.path.join(settings.certificate_dir, f"{safe}.pdf")

    doc = SimpleDocTemplate(path, pagesize=A4, topMargin=12 * mm, bottomMargin=15 * mm,
                            leftMargin=14 * mm, rightMargin=14 * mm)
    story = []

    right_cell = [_P("Mushak-6.6", 9, TA_RIGHT, bold=True)]
    if os.path.exists(_LOGO):
        img = Image(_LOGO, width=24 * mm, height=24 * mm)
        right_cell = [_P("Mushak-6.6", 9, TA_RIGHT, bold=True), Spacer(1, 3), img]
    center = [
        _P("Government of the People's Republic of Bangladesh", 11, TA_CENTER, bold=True),
        _P("National Board of Revenue", 10, TA_CENTER, bold=True), Spacer(1, 3),
        _P("Withholding Tax Certificate", 11, TA_CENTER, bold=True),
        _P("(See clause (Cha) of Sub-Rule (1) of Rule 40)", 8, TA_CENTER),
    ]
    head = Table([[_P("", 8), center, right_cell]], colWidths=[26 * mm, 130 * mm, 26 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, 0), "TOP"), ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [head, Spacer(1, 8)]

    issuer_tbl = Table([
        [_P("Name of withholding entity"), _P(f": {issuer.name}")],
        [_P("Address of withholding entity"), _P(f": {issuer.address or ''}")],
        [_P("BIN of withholding entity (if applicable)"), _P(f": {issuer.bin or ''}")],
    ], colWidths=[62 * mm, 120 * mm])
    issuer_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [issuer_tbl, Spacer(1, 6)]

    issue = cert.issue_date.strftime("%d/%m/%Y")
    story.append(Table([[_P(f"Certificate No: {cert.certificate_no}", 9, bold=True),
                         _P(f"Date of Issue: {issue}", 9, TA_RIGHT, bold=True)]],
                       colWidths=[110 * mm, 72 * mm]))
    story.append(Spacer(1, 8))

    body = ("This is to certify that VAT has been deducted at source from the supplies having VAT "
            "deductible at source in accordance with Section 49 of the Act. The VAT so deducted has "
            "been deposited in the government treasury by book transfer / treasury challan / increasing "
            "adjustment in the return. A copy has been attached (if applicable).")
    story += [_P(body, 9, TA_LEFT, lead=13), Spacer(1, 10)]

    h = lambda s: _P(s, 7.5, TA_CENTER, bold=True)
    c = lambda s: _P(s, 8, TA_CENTER)
    r = lambda s: _P(s, 8, TA_RIGHT)
    bin_ = supplier.bin if cert.has_bin else ""
    total_vat = money(cert.total_vat)
    data = [
        [h("SL\nNO"), h("Supplier"), "", h("Treasury Challan"), "", h("Concerned\ntax invoice"), "",
         h("Total Value\nof Supply*"), h("Amount of\nVAT (Taka)"), h("Amount of VAT\nwithheld at source\n(Taka)")],
        ["", h("Name"), h("BIN"), h("Number"), h("Date"), h("Number"), h("Date"), "", "", ""],
    ]
    for i, ln in enumerate(lines):
        data.append([c(str(i + 1)), c(supplier.name), c(bin_), c(ln["challan"]), c(ln["cdate"]),
                     c(ln.get("inv", "")), c(ln.get("idate", "")),
                     r(money(ln["value_incl"])), r(money(ln["vat"])),
                     r(total_vat if i == 0 else "")])
    challans = " & ".join(ln["challan"] for ln in lines if ln["challan"])
    cdate = lines[0]["cdate"] if lines else ""
    data.append([_P(f"is paid through treasury challan no. {challans} Dated {cdate} which amounts to "
                    f"BDT {total_vat}", 7.5, TA_LEFT, lead=10)] + [""] * 9)
    data.append([_P("Total", 8, TA_RIGHT, bold=True)] + [""] * 6 +
                [r(money(cert.total_value_incl)), r(total_vat), ""])

    cw = [10 * mm, 26 * mm, 15 * mm, 26 * mm, 16 * mm, 16 * mm, 14 * mm, 20 * mm, 17 * mm, 22 * mm]
    grid = Table(data, colWidths=cw)
    grid.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (2, 0)), ("SPAN", (3, 0), (4, 0)), ("SPAN", (5, 0), (6, 0)),
        ("SPAN", (7, 0), (7, 1)), ("SPAN", (8, 0), (8, 1)), ("SPAN", (9, 0), (9, 1)),
        ("SPAN", (0, len(data) - 2), (8, len(data) - 2)),
        ("SPAN", (0, len(data) - 1), (6, len(data) - 1)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.whitesmoke),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [grid, Spacer(1, 26)]

    # single Officer-in-Charge block (matches the Excel 'Cerificate' tab)
    name = (issuer.signatures[0].name if issuer.signatures else None) or issuer.officer_name or ""
    desig = (issuer.signatures[0].designation if issuer.signatures else None) or issuer.officer_designation or ""
    sig = Table([[_P("Officer-in-Charge", 9, bold=True)], [_P("Signature", 9)], [Spacer(1, 20)],
                 [_P(name, 9, bold=True)], [_P(desig, 9)]], colWidths=[85 * mm])
    sig.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [sig, Spacer(1, 10), _P("*Price inclusive of VAT and SD (if any).", 8, TA_LEFT)]

    doc.build(story)
    return path
