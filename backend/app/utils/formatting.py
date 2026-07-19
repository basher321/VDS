"""Money / date / fiscal-year formatting helpers."""
from datetime import date
from decimal import Decimal, ROUND_HALF_UP


def money(v) -> str:
    if v is None:
        return ""
    d = Decimal(str(v))
    if d == d.to_integral_value():
        return f"{int(d):,}"
    return f"{d:,.2f}"


def money2(v) -> str:
    """Always 2 decimals, comma-grouped -- matches the Certificate tab's accounting format."""
    if v is None:
        return ""
    return f"{Decimal(str(v)):,.2f}"


def round2(v) -> Decimal:
    return Decimal(str(v)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def dmy(d: date | None) -> str:
    return d.strftime("%d/%m/%Y") if d else ""


def dmy_words(d: date | None) -> str:
    """e.g. '14 Jan 2024' -- matches the Certificate tab's table date format."""
    return d.strftime("%d %b %Y").lstrip("0") if d else ""


def issue_dmy(d: date | None) -> str:
    """e.g. '14-Jan-24' -- matches the Certificate tab's 'Date of Issue' format."""
    return d.strftime("%d-%b-%y") if d else ""


def fiscal_year(d: date) -> str:
    """Bangladesh fiscal year (Jul-Jun), e.g. 2023-24 for a Jan-2024 date."""
    start = d.year if d.month >= 7 else d.year - 1
    return f"{start}-{str(start + 1)[-2:]}"
