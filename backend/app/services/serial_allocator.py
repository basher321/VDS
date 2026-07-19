"""Atomic, gapless certificate-number allocation per issuer + scope."""
from sqlalchemy import text
from sqlalchemy.orm import Session
from ..models.organization import NumberingConfig, Issuer


def _fy(period: str, fmt: str) -> str:
    start, end2 = period.split("-")
    if fmt == "YYYY":
        return start
    if fmt == "YY-YY":
        return f"{start[-2:]}-{end2}"
    return f"{start}-{end2}"


def _render(fmt: str, company: str, fy: str, number: str, sep: str, month: str = "") -> str:
    return (fmt.replace("{CompanyName}", company)
               .replace("{FiscalYear}", fy)
               .replace("{Month}", month)
               .replace("{AutoNumber}", number)
               .replace("{sep}", sep))


def get_numbering(db: Session, issuer_id: int) -> NumberingConfig:
    cfg = db.query(NumberingConfig).filter(NumberingConfig.issuer_id == issuer_id).first()
    if not cfg:
        issuer = db.get(Issuer, issuer_id)
        cfg = NumberingConfig(issuer_id=issuer_id, company_token=issuer.name if issuer else "VDS")
        db.add(cfg)
        db.flush()
    return cfg


def allocate_number(db: Session, issuer_id: int, period: str, month: str = "") -> str:
    """month: e.g. 'December', for number_format strings using the {Month} token."""
    cfg = get_numbering(db, issuer_id)
    scope = f"i{issuer_id}:{period if cfg.reset_policy == 'per_fiscal_year' else 'global'}"
    db.execute(text("INSERT INTO number_sequences (scope, last_value) VALUES (:s, :seed) "
                    "ON CONFLICT (scope) DO NOTHING"),
               {"s": scope, "seed": cfg.start_number - 1})
    value = db.execute(text("UPDATE number_sequences SET last_value = last_value + 1 "
                            "WHERE scope = :s RETURNING last_value"), {"s": scope}).scalar_one()
    number = str(value).zfill(cfg.pad_width)
    return _render(cfg.number_format, cfg.company_token, _fy(period, cfg.fiscal_year_format),
                   number, cfg.separator, month)
