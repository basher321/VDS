"""Core VDS math. The base is derived from the deducted VAT and the rate:

    value_excl = deducted_vat / rate
    value_incl = value_excl + deducted_vat   (price inclusive of VAT/SD)

Matches the Mushak-6.6 sheet, where 'Total Value of Supply*' is VAT-inclusive.
"""
from decimal import Decimal
from ..utils.formatting import round2


def derive(deducted_vat, rate) -> dict:
    vat = Decimal(str(deducted_vat))
    r = Decimal(str(rate))
    if r <= 0:
        raise ValueError("VAT rate must be greater than zero")
    if vat <= 0:
        raise ValueError("Deducted VAT must be greater than zero")
    excl = round2(vat / r)
    return {"value_excl": excl, "value_incl": round2(excl + vat)}


def totals(lines) -> dict:
    """lines: iterable of objects/dicts with value_incl, vat, withheld."""
    tv = sum(Decimal(str(getattr(l, "value_incl", l.get("value_incl")))) for l in lines)
    tvat = sum(Decimal(str(getattr(l, "vat_amount", None) or l.get("vat"))) for l in lines) \
        if False else None
    # keep explicit to avoid attribute ambiguity
    total_incl = Decimal("0")
    total_vat = Decimal("0")
    for l in lines:
        total_incl += Decimal(str(l["value_incl"] if isinstance(l, dict) else l.value_incl))
        total_vat += Decimal(str(l["vat"] if isinstance(l, dict) else l.vat_amount))
    return {"total_incl": round2(total_incl), "total_vat": round2(total_vat)}
