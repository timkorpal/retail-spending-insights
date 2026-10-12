"""Calculate weekly metrics using PostgreSQL aggregations."""

from datetime import date

from sqlalchemy import Date, cast, func, select
from sqlalchemy.orm import Session

from models import Transaction


def list_merchants(session: Session) -> list[str]:
    """Return distinct merchant names in alphabetical order."""

    statement = (
        select(Transaction.merchant_name)
        .distinct()
        .order_by(Transaction.merchant_name)
    )

    return list(session.scalars(statement).all())


def merchant_exists(session: Session, merchant_name: str) -> bool:
    """Check whether the merchant has any stored transactions."""

    statement = (
        select(Transaction.id)
        .where(Transaction.merchant_name == merchant_name)
        .limit(1)
    )

    return session.scalar(statement) is not None


def get_weekly_metrics(
    session: Session,
    merchant_name: str,
    start_date: date | None = None,
    end_date: date | None = None,
) -> list[dict]:
    """
    Group a merchant's transactions into Monday-based weeks.

    Date filters are inclusive and apply before aggregation.
    Negative amounts represent refunds; zero amounts are neither
    purchases nor refunds.

    Only weeks containing transactions are returned.
    """

    # PostgreSQL date_trunc('week', ...) finds the Monday of each week.
    # Cast the result to DATE for our response schema.
    week_start = cast(
        func.date_trunc("week", Transaction.transaction_date),
        Date,
    ).label("week_start")

    is_purchase = Transaction.amount > 0
    is_refund = Transaction.amount < 0

    statement = (
        select(
            week_start,

            # Sum positive amounts. Use zero when none exist.
            func.coalesce(
                func.sum(Transaction.amount).filter(is_purchase),
                0,
            ).label("gross_purchase_spending"),

            # Convert the sum of negative amounts into a positive
            # refund total for easier interpretation.
            func.coalesce(
                -func.sum(Transaction.amount).filter(is_refund),
                0,
            ).label("refund_amount"),

            # Purchases plus negative refunds gives net spending.
            func.sum(Transaction.amount).label(
                "net_observed_spending"
            ),

            # Count purchases rather than all records.
            func.count(Transaction.id).filter(
                is_purchase
            ).label("purchase_count"),

            # Count each purchasing customer once per week.
            func.count(
                func.distinct(Transaction.customer_id)
            ).filter(is_purchase).label(
                "unique_purchasing_customers"
            ),

            # Average positive purchases, rounded to cents.
            # PostgreSQL returns NULL when there are no purchases.
            func.round(
                func.avg(Transaction.amount).filter(is_purchase),
                2,
            ).label("average_purchase_amount"),
        )
        .where(Transaction.merchant_name == merchant_name)
    )

    if start_date is not None:
        statement = statement.where(
            Transaction.transaction_date >= start_date
        )

    if end_date is not None:
        statement = statement.where(
            Transaction.transaction_date <= end_date
        )

    statement = (
        statement
        .group_by(week_start)
        .order_by(week_start)
    )

    # mappings() returns column names and values rather than ORM objects.
    return [
        dict(row)
        for row in session.execute(statement).mappings()
    ]