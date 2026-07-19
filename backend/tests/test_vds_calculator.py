from decimal import Decimal
from app.services.vds_calculator import derive


def test_derive_consultant_15pct():
    d = derive(30000, 0.15)
    assert d["value_excl"] == Decimal("200000.00")
    assert d["value_incl"] == Decimal("230000.00")


def test_derive_stationery_7_5pct():
    d = derive(91.5, 0.075)
    assert d["value_excl"] == Decimal("1220.00")
    assert d["value_incl"] == Decimal("1311.50")


def test_derive_rejects_zero_rate():
    try:
        derive(100, 0)
        assert False
    except ValueError:
        assert True
