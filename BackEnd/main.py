"""FastAPI endpoints for synthetic retail spending analysis."""

from datetime import date
from typing import Annotated

from fastapi import Depends, FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database import SessionLocal
from schemas import WeeklyMetric
from services.metrics import (
    get_weekly_metrics,
    list_merchants,
    merchant_exists,
)


app = FastAPI(
    title="Retail Spending Insights",
    description=(
        "Analyze synthetic transaction data. "
        "Metrics represent observed spending, not company revenue."
    ),
)

# Allow the local Vite frontend to call the backend.
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


def get_db():
    """
    Provide a database session for one request.

    The context manager closes the session after the request,
    including when an exception occurs.
    """

    with SessionLocal() as session:
        yield session


DatabaseSession = Annotated[Session, Depends(get_db)]


@app.get("/merchants", response_model=list[str])
def get_merchants(db: DatabaseSession):
    """List merchant names available in the transaction dataset."""

    return list_merchants(db)


@app.get(
    "/merchants/{merchant_name}/weekly-metrics",
    response_model=list[WeeklyMetric],
)
def weekly_metrics(
    merchant_name: str,
    db: DatabaseSession,
    start_date: Annotated[
        date | None,
        Query(description="Inclusive start date, such as 2026-07-01"),
    ] = None,
    end_date: Annotated[
        date | None,
        Query(description="Inclusive end date, such as 2026-09-30"),
    ] = None,
):
    """
    Retrieve spending metrics grouped into weeks beginning Monday.

    Date filters can produce partial weeks. Missing weeks are omitted,
    and results do not establish whether source coverage is complete.
    """

    if (
        start_date is not None
        and end_date is not None
        and start_date > end_date
    ):
        raise HTTPException(
            status_code=422,
            detail="start_date must be on or before end_date.",
        )

    if not merchant_exists(db, merchant_name):
        raise HTTPException(
            status_code=404,
            detail=f"Merchant '{merchant_name}' not found.",
        )

    return get_weekly_metrics(
        session=db,
        merchant_name=merchant_name,
        start_date=start_date,
        end_date=end_date,
    )