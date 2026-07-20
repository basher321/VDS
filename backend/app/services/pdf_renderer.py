"""Render a Certificate to a Mushak-6.6 PDF matching the source workbook's 'Cerificate' tab:
government header (national emblem left, centred NBR title, issuer logo + 'Mushak-6.6' label
right); issuer identity block; Certificate No / Date of Issue; Section-49 body; the bordered
deduction table (SL / Supplier Name+BIN / Treasury Challan No+Date / Concerned tax invoice
No+Date / Total Value of Supply* / Amount of VAT / Amount withheld at source) where the
withheld total is printed once against the first line and the remaining line rows carry the
treasury-payment narrative in that same column, exactly as the template does it; a Total row;
then the Officer-in-Charge signature block with the signatory's scanned signature and the
issuer's seal, name and designation; footnote.
"""
import os
from io import BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import mm
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT, TA_JUSTIFY
from reportlab.platypus import (SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image)
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from . import storage
from ..utils.formatting import money2, dmy, dmy_words, issue_dmy

_ASSETS = os.path.join(os.path.dirname(__file__), "..", "assets", "logo")
_NATIONAL_EMBLEM = os.path.join(_ASSETS, "national_emblem.png")
_DEFAULT_LOGO = os.path.join(_ASSETS, "issuer_logo.png")

# The source workbook sets every certificate cell in Garamond. Register it from the Windows
# font folder if present; otherwise fall back to Times (the closest ReportLab built-in serif)
# so the PDF still renders correctly on machines without that font installed.
_FONT_REG, _FONT_BOLD = "Times-Roman", "Times-Bold"
try:
    _reg = r"C:\Windows\Fonts\GARA.TTF"
    _bold = r"C:\Windows\Fonts\GARABD.TTF"
    if os.path.exists(_reg) and os.path.exists(_bold):
        pdfmetrics.registerFont(TTFont("Garamond", _reg))
        pdfmetrics.registerFont(TTFont("Garamond-Bold", _bold))
        _FONT_REG, _FONT_BOLD = "Garamond", "Garamond-Bold"
except Exception:
    pass


def _P(t, fs=10, al=TA_LEFT, bold=False, lead=None):
    fn = _FONT_BOLD if bold else _FONT_REG
    return Paragraph(str(t), ParagraphStyle("x", fontName=fn, fontSize=fs, alignment=al, leading=lead or fs + 2))


def _local_img_or_none(path, w, h):
    """For assets bundled with the app itself (not user-uploaded) -- always a plain local
    file next to the code, so it works the same whether storage is local disk or Supabase."""
    if path and os.path.exists(path):
        try:
            return Image(path, width=w, height=h)
        except Exception:
            return None
    return None


def _stored_img_or_none(stored_path, w, h):
    """For user-uploaded images (issuer seal/logo, signatory's signature), fetched through
    the storage abstraction so this works whether it's on local disk or Supabase Storage."""
    data = storage.load(stored_path)
    if not data:
        return None
    try:
        return Image(BytesIO(data), width=w, height=h)
    except Exception:
        return None


def render_certificate_pdf(cert, issuer, supplier, lines) -> str:
    """lines: list of dicts {challan, cdate (date|None), inv, idate (date|None), value_incl, vat}.
    Returns a value to store as cert.pdf_path and pass to storage.load() later."""
    buf = BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4, topMargin=12 * mm, bottomMargin=15 * mm,
                            leftMargin=14 * mm, rightMargin=10 * mm)
    story = []

    # ---- header: national emblem / centred government title / issuer logo ----
    emblem = _local_img_or_none(_NATIONAL_EMBLEM, 18 * mm, 19 * mm)
    left_cell = [emblem] if emblem else [_P("", 8)]

    logo = _stored_img_or_none(issuer.letterhead_header_path, 24 * mm, 24 * mm) or \
        _local_img_or_none(_DEFAULT_LOGO, 24 * mm, 24 * mm)
    right_cell = [_P("Mushak-6.6", 9, TA_RIGHT, bold=True)]
    if logo:
        right_cell += [Spacer(1, 3), logo]

    center = [
        _P("Government of the People's Republic of Bangladesh", 11, TA_CENTER, bold=True),
        _P("National Board of Revenue", 10, TA_CENTER, bold=True), Spacer(1, 3),
        _P("Withholding Tax Certificate", 11, TA_CENTER, bold=True),
        _P("(See clause (Cha) of Sub-Rule (1) of Rule 40)", 8, TA_CENTER),
    ]
    head = Table([[left_cell, center, right_cell]], colWidths=[26 * mm, 136 * mm, 26 * mm])
    head.setStyle(TableStyle([("VALIGN", (0, 0), (-1, 0), "TOP"), ("ALIGN", (0, 0), (0, 0), "LEFT"),
                              ("ALIGN", (2, 0), (2, 0), "RIGHT"),
                              ("LEFTPADDING", (0, 0), (-1, -1), 0), ("RIGHTPADDING", (0, 0), (-1, -1), 0)]))
    story += [head, Spacer(1, 8)]

    # ---- issuer identity ----
    issuer_tbl = Table([
        [_P("Name of withholding entity"), _P(f": {issuer.name}")],
        [_P("Address of withholding entity"), _P(f": {issuer.address or ''}")],
        [_P("BIN of withholding entity (if applicable)"), _P(f": {issuer.bin or ''}")],
    ], colWidths=[62 * mm, 124 * mm])
    issuer_tbl.setStyle(TableStyle([("VALIGN", (0, 0), (-1, -1), "TOP"), ("BOTTOMPADDING", (0, 0), (-1, -1), 3)]))
    story += [issuer_tbl, Spacer(1, 6)]

    # ---- certificate no / date of issue ----
    story.append(Table([[_P(f"Certificate No: {cert.certificate_no}", 10),
                         _P(f"Date of Issue: {issue_dmy(cert.issue_date)}", 10, TA_RIGHT)]],
                       colWidths=[110 * mm, 78 * mm]))
    story.append(Spacer(1, 8))

    # ---- body ----
    body = ("This is to certify that VAT has been deducted at source from the supplies having VAT "
            "deductible at source in accordance with Section 49 of the Act. The VAT so deducted has "
            "been deposited in the government treasury by book transfer/ treasury challan/ increasing "
            "adjustment in the return. A copy has been attached (if applicable).")
    story += [_P(body, 10, TA_JUSTIFY, lead=14), Spacer(1, 10)]

    # ---- deduction table ----
    h = lambda s: _P(s, 8, TA_CENTER, bold=True)
    c = lambda s: _P(s, 9, TA_CENTER)
    r = lambda s: _P(s, 9, TA_RIGHT)
    bin_ = supplier.bin if (cert.has_bin and supplier.bin) else ""
    total_vat_str = money2(cert.total_vat)

    data = [
        [h("SL NO"), h("Supplier"), "", h("Treasury Challan"), "", h("Concerned\ntax invoice"), "",
         h("Total Value\nof Supply*"), h("Amount of VAT\n(Taka)"), h("Amount of VAT\nwithheld at source\n(Taka)")],
        ["", h("Name"), h("BIN"), h("Number"), h("Date"), h("Number"), h("Date"), "", "", ""],
    ]
    n = len(lines)
    for i, ln in enumerate(lines):
        withheld = r(total_vat_str) if i == 0 else ""
        data.append([c(str(i + 1)), c(supplier.name), c(bin_), c(ln["challan"]), c(dmy_words(ln["cdate"])),
                     c(ln.get("inv", "")), c(dmy_words(ln.get("idate"))),
                     r(money2(ln["value_incl"])), r(money2(ln["vat"])), withheld])

    challans = " & ".join(ln["challan"] for ln in lines if ln["challan"])
    narrative_text = (f"is paid through treasury challan no. {challans} Dated {dmy(lines[0]['cdate']) if lines else ''} "
                      f"which amounts to BDT {total_vat_str}")

    extra_spans = []
    if n > 1:
        # column J (index 9), rows for line 2..line N: one merged cell carrying the narrative,
        # exactly as the template merges J26:J30 beside the SL 2+ rows.
        j_start, j_end = 3, n + 1
        data[j_start][9] = _P(narrative_text, 9, TA_LEFT, lead=11)
        extra_spans.append(("SPAN", (9, j_start), (9, j_end)))
        extra_spans.append(("VALIGN", (9, j_start), (9, j_end), "TOP"))

    data.append([_P("Total", 9, TA_RIGHT, bold=True)] + [""] * 6 +
                [r(money2(cert.total_value_incl)), r(total_vat_str), ""])
    total_row = len(data) - 1

    cw = [10 * mm, 26 * mm, 15 * mm, 26 * mm, 16 * mm, 16 * mm, 14 * mm, 20 * mm, 17 * mm, 22 * mm]
    grid = Table(data, colWidths=cw)
    grid.setStyle(TableStyle([
        ("GRID", (0, 0), (-1, -1), 0.6, colors.black), ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("SPAN", (0, 0), (0, 1)), ("SPAN", (1, 0), (2, 0)), ("SPAN", (3, 0), (4, 0)), ("SPAN", (5, 0), (6, 0)),
        ("SPAN", (7, 0), (7, 1)), ("SPAN", (8, 0), (8, 1)), ("SPAN", (9, 0), (9, 1)),
        *extra_spans,
        ("SPAN", (0, total_row), (6, total_row)),
        ("BACKGROUND", (0, 0), (-1, 1), colors.whitesmoke),
        ("TOPPADDING", (0, 0), (-1, -1), 3), ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))
    story += [grid]
    if n == 1:
        # the template only demonstrates this narrative merged beside a 2nd+ line item; with a
        # single line there's no such row to merge it into, so it's appended as a note instead.
        story += [Spacer(1, 4), _P(narrative_text, 8, TA_LEFT)]
    story += [Spacer(1, 22)]

    # ---- Officer-in-Charge signature block ----
    sig = issuer.signatures[0] if issuer.signatures else None
    sig_name = (sig.name if sig else None) or issuer.officer_name or ""
    sig_desig = (sig.designation if sig else None) or issuer.officer_designation or ""
    sig_img = _stored_img_or_none(sig.image_path if sig else None, 30 * mm, 15 * mm)
    seal_img = _stored_img_or_none(issuer.seal_path, 22 * mm, 22 * mm)

    rows = [[_P("Officer-in-Charge", 10, bold=True)], [_P("Signature", 10)]]
    if sig_img or seal_img:
        inner = Table([[sig_img or "", seal_img or ""]], colWidths=[38 * mm, 25 * mm])
        inner.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0), ("VALIGN", (0, 0), (-1, -1), "BOTTOM")]))
        rows.append([inner])
    else:
        rows.append([Spacer(1, 20)])
    rows += [[_P(sig_name, 10, bold=True)], [_P(sig_desig, 10)]]
    sig_tbl = Table(rows, colWidths=[85 * mm], hAlign="LEFT")
    sig_tbl.setStyle(TableStyle([("LEFTPADDING", (0, 0), (-1, -1), 0)]))
    story += [sig_tbl, Spacer(1, 10), _P("*Price inclusive of VAT and SD (if any).", 10, TA_LEFT)]

    doc.build(story)
    safe = cert.certificate_no.replace("/", "_").replace("\\", "_")
    return storage.save("certificates", f"{safe}.pdf", buf.getvalue())
