"""
Import validated CSV transactions into PostgreSQL.

Duplicate transaction IDs are skipped using ON CONFLICT DO NOTHING.
All insert batches run in one database transaction. If a batch fails,
the entire database import is rolled back.
"""

from pathlib import Path

from sqlalchemy.dialects.postgresql import insert

from database import SessionLocal
from models import Transaction
from services.transactions import load_transactions


PROJECT_ROOT = Path(__file__).resolve().parent.parent
CSV_PATH = PROJECT_ROOT / "data" / "synthetic_retail_transactions.csv"

# Insert manageable groups rather than issuing one query per record.
BATCH_SIZE = 500


def main() -> None:
    """Validate the CSV, insert new records, and print import counts."""

    transactions, rejected_rows = load_transactions(CSV_PATH)

    print(f"Validated: {len(transactions):,}")
    print(f"Rejected: {len(rejected_rows):,}")

    inserted_count = 0

    # Creates a session and begins a database transaction.
    # Successful completion commits automatically.
    # An exception rolls back the transaction and closes the session.
    with SessionLocal.begin() as session:

        for start in range(0, len(transactions), BATCH_SIZE):
            batch = transactions[start:start + BATCH_SIZE]

            # Build a PostgreSQL INSERT for the current batch.
            #
            # Existing transaction IDs are skipped without replacing
            # their values. Other database errors still fail the import.
            statement = (
                insert(Transaction)
                .values(batch)
                .on_conflict_do_nothing(
                    index_elements=["transaction_id"]
                )
                .returning(Transaction.transaction_id)
            )

            # RETURNING provides IDs only for rows actually inserted.
            inserted_ids = session.execute(statement).scalars().all()
            inserted_count += len(inserted_ids)

    # This summary runs after the database transaction commits.
    skipped_count = len(transactions) - inserted_count

    print(f"\nInserted: {inserted_count:,}")
    print(f"Already stored: {skipped_count:,}")

    if rejected_rows:
        print("\nFirst five rejected rows:")

        for rejected in rejected_rows[:5]:
            print(rejected)


if __name__ == "__main__":
    main()