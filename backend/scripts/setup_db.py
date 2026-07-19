"""One-time local setup: create all tables, fix the two generated columns that
SQLAlchemy's create_all() can't express, and seed an admin user. Safe to re-run --
every step checks current state before changing anything.

Usage (from backend/, with the virtualenv active):
    python scripts/setup_db.py
    python scripts/setup_db.py --username admin --password Admin123
"""
import argparse
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import text

from app.core.database import Base, engine, SessionLocal
from app.core.security import hash_password
from app import models  # noqa: F401 -- populates Base.metadata
from app.models.organization import User


def ensure_tables():
    Base.metadata.create_all(engine)
    print("[ok] tables created/verified")


def ensure_generated_columns():
    """invoices.value_excl / value_incl must be DB-computed (see app/models/invoice.py).
    create_all() has no way to express GENERATED ALWAYS AS, so add it here if missing."""
    with engine.begin() as conn:
        state = conn.execute(text(
            "select is_generated from information_schema.columns "
            "where table_name = 'invoices' and column_name = 'value_excl'"
        )).scalar()
        if state == "ALWAYS":
            print("[ok] invoices.value_excl / value_incl already generated columns")
            return
        conn.execute(text("ALTER TABLE invoices DROP COLUMN IF EXISTS value_excl"))
        conn.execute(text("ALTER TABLE invoices DROP COLUMN IF EXISTS value_incl"))
        conn.execute(text(
            "ALTER TABLE invoices ADD COLUMN value_excl numeric(18,2) "
            "GENERATED ALWAYS AS (round(deducted_vat / vat_rate, 2)) STORED"))
        conn.execute(text(
            "ALTER TABLE invoices ADD COLUMN value_incl numeric(18,2) "
            "GENERATED ALWAYS AS (round(deducted_vat / vat_rate, 2) + deducted_vat) STORED"))
        print("[ok] invoices.value_excl / value_incl converted to generated columns")


def ensure_admin_user(username: str, password: str):
    db = SessionLocal()
    try:
        if db.query(User).filter(User.username == username).first():
            print(f"[ok] user '{username}' already exists")
            return
        db.add(User(username=username, password_hash=hash_password(password),
                    full_name="Administrator", role="admin", is_active=True))
        db.commit()
        print(f"[ok] created user -> username={username} password={password}")
    finally:
        db.close()


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--username", default="admin")
    p.add_argument("--password", default="Admin123")
    args = p.parse_args()

    ensure_tables()
    ensure_generated_columns()
    ensure_admin_user(args.username, args.password)
    print("done.")
