"""Gapless certificate-number allocator (one row per scope)."""
from sqlalchemy import Integer, String
from sqlalchemy.orm import Mapped, mapped_column
from ..core.database import Base


class NumberSequence(Base):
    __tablename__ = "number_sequences"
    scope: Mapped[str] = mapped_column(String(40), primary_key=True)  # 'i1:2023-24'
    last_value: Mapped[int] = mapped_column(Integer, default=0)
