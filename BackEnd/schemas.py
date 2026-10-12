"""Define the response structure for weekly merchant metrics."""

from datetime import date
from decimal import Decimal

from pydantic import BaseModel


class WeeklyMetric(BaseModel):
    # Weeks begin on Monday.
    week_start: date

    gross_purchase_spending: Decimal
    refund_amount: Decimal
    net_observed_spending: Decimal

    purchase_count: int
    unique_purchasing_customers: int

    # None when the week contains no positive purchases.
    average_purchase_amount: Decimal | None