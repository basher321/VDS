from app.services.validators import valid_issuer_bin, valid_email, valid_whatsapp, validate_import_row


def test_bin_format():
    assert valid_issuer_bin("004870109-0208")
    assert not valid_issuer_bin("12345")


def test_email_and_whatsapp():
    assert valid_email("a@b.com")
    assert not valid_email("nope")
    assert valid_whatsapp("+8801711000001")
    assert not valid_whatsapp("12")


def test_import_row_rules():
    assert validate_import_row({"supplier_name": "X", "deducted_vat": 100, "vat_rate": 0.1}) is None
    assert validate_import_row({"supplier_name": "X", "deducted_vat": 0, "vat_rate": 0}) is not None
    assert validate_import_row({"supplier_name": "", "deducted_vat": 100, "vat_rate": 0.1}) is not None
