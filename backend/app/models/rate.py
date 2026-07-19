"""VDS rate master: service category -> applicable rate (versioned)."""
from datetime import date, datetime
from sqlalchemy import Date, DateTime, Numeric, String, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class VdsRate(Base):
    __tablename__ = "vds_rates"
    __table_args__ = (UniqueConstraint("category_code", "effective_from"),)
    id: Mapped[int] = mapped_column(primary_key=True)
    category_code: Mapped[str] = mapped_column(String(30))
    description: Mapped[str] = mapped_column(String(200))
    vds_rate: Mapped[float] = mapped_column(Numeric(6, 4))
    base_rule: Mapped[str] = mapped_column(String(20), default="deduct")
    effective_from: Mapped[date] = mapped_column(Date, default=date(2023, 7, 1))
    effective_to: Mapped[date | None] = mapped_column(Date)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
