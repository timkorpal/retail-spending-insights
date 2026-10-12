"""
SQLAlchemy model for validated retail transactions.

The unique transaction_id constraint prevents duplicate transactions
from being stored, including when the same CSV is imported again.
"""

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import (
    Date,
    DateTime,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from database import Base


class Transaction(Base):
    """A single purchase or refund from our synthetic dataset."""

    __tablename__ = "transactions"

    # Internal database identifier.
    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
    )

    # Source identifier used to prevent duplicate imports.
    transaction_id: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
    )

    # Fictional customer identifier.
    customer_id: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    merchant_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Date of the transaction, rather than the date we imported it.
    transaction_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        index=True,
    )

    # NUMERIC stores exact decimal amounts.
    # Precision 12 allows 12 total digits, including 2 decimal places.
    # Negative amounts can represent refunds.
    amount: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
    )

    # PostgreSQL supplies the ingestion timestamp when inserting a row.
    ingested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )