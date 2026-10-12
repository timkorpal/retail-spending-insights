"""
Read and validate transaction records from a CSV file.

Required CSV columns:
    transaction_id, customer_id, merchant_name, transaction_date, amount

Each accepted record contains:
    - Nonempty transaction, customer, and merchant identifiers.
    - A transaction date converted to a Python date object.
    - A finite amount converted to Decimal, with no fractional cents.

Rows that fail validation are collected separately with their CSV
record number and rejection reason.

Duplicate detection applies only to accepted records within this file.
This function does not check PostgreSQL or previously imported files.

The CSV file is read without being modified.
"""

# Python's built-in module for reading and writing CSV files.
import csv

# Used to convert date text into Python date objects.
from datetime import date

# Decimal supports decimal arithmetic without the binary rounding
# behavior of floats. InvalidOperation handles invalid conversions
# and decimal operations.
from decimal import Decimal, InvalidOperation

# Represents the path to the CSV file.
from pathlib import Path


def load_transactions(file_path: Path) -> tuple[list[dict], list[dict]]:
    """
    Read a transaction CSV and separate accepted and rejected records.

    Args:
        file_path:
            Path object identifying the CSV file to read.

    Returns:
        A tuple containing two lists:

        transactions:
            Validated transaction dictionaries. Dates are date objects,
            and monetary amounts are Decimal objects.

        rejected_rows:
            Dictionaries containing the row number and rejection reason.

    Raises:
        FileNotFoundError:
            If the CSV file does not exist.

        ValueError:
            If one or more required columns are missing.

        OSError:
            If the file cannot be opened or read.

    Individual row validation failures are recorded in rejected_rows
    rather than stopping the entire import.
    """

    # Store records that successfully pass every validation check.
    transactions = []

    # Store the row number and reason for each rejected record.
    rejected_rows = []

    # Track transaction IDs belonging to accepted records.
    #
    # A set provides efficient membership checks and stores unique values.
    # This set is recreated every time the function is called.
    seen_ids = set()

    # Open the CSV file for reading.
    #
    # newline="":
    #     Lets the csv module handle newline characters correctly,
    #     including newlines inside quoted fields.
    #
    # encoding="utf-8-sig":
    #     Reads UTF-8 text and removes a leading byte order mark (BOM)
    #     if present. Some spreadsheet exports include this mark.
    #
    # The with statement closes the file automatically when the block
    # finishes, including when an exception occurs.
    with file_path.open(newline="", encoding="utf-8-sig") as file:

        # Interpret the first CSV record as column headers.
        #
        # Each subsequent record becomes a dictionary:
        #     {"transaction_id": "TX000001", "amount": "42.50", ...}
        #
        # CSV values initially arrive as strings.
        reader = csv.DictReader(file)

        # Define the columns that must exist in the header.
        # Additional columns are allowed but are not used here.
        required_columns = {
            "transaction_id",
            "customer_id",
            "merchant_name",
            "transaction_date",
            "amount",
        }

        # fieldnames contains the CSV headers.
        # It can be None when the file is empty.
        #
        # "or []" provides an empty list when no headers are available.
        # issubset() checks that every required column is present.
        #
        # This check is outside the row-level try/except because missing
        # columns prevent the file from being processed correctly.
        if not required_columns.issubset(reader.fieldnames or []):
            raise ValueError("CSV is missing required columns.")

        # Process each data record and assign it a number.
        #
        # Start at 2 because record 1 contains the headers.
        # For ordinary single-line CSV records, this matches the file
        # line number. Blank lines or multiline fields can make the
        # physical line number differ.
        for row_number, row in enumerate(reader, start=2):
            try:

                # Extract identifying fields and remove surrounding spaces.
                #
                # A short CSV record can produce None for a missing field.
                # "or ''" converts that value into an empty string so
                # strip() can be called safely.
                transaction_id = (row["transaction_id"] or "").strip()
                customer_id = (row["customer_id"] or "").strip()
                merchant_name = (row["merchant_name"] or "").strip()

                # all() returns True only when every value is truthy.
                # Empty strings are false, so any missing identifier
                # causes this row to be rejected.
                if not all((transaction_id, customer_id, merchant_name)):
                    raise ValueError(
                        "Transaction, customer, and merchant are required."
                    )

                # Reject a transaction ID already accepted from this file.
                #
                # Invalid earlier rows do not reserve their IDs because
                # IDs are added to seen_ids only after successful validation.
                if transaction_id in seen_ids:
                    raise ValueError("Duplicate transaction ID.")

                # Convert the date string into a date object.
                #
                # Expected input example:
                #     "2026-07-01"
                #
                # Invalid dates, such as "2026-02-30", raise ValueError.
                transaction_date = date.fromisoformat(
                    (row["transaction_date"] or "").strip()
                )

                # Convert the amount directly from text into Decimal.
                #
                # Example:
                #     "42.50" becomes Decimal("42.50").
                #
                # Avoid converting through float first, which can introduce
                # binary rounding artifacts.
                # Invalid numeric text raises InvalidOperation.
                amount = Decimal((row["amount"] or "").strip())

                # Reject special Decimal values such as NaN and Infinity.
                # Negative values are permitted so refunds can be represented.
                # Zero is also permitted by this validation.
                if not amount.is_finite():
                    raise ValueError("Amount must be a finite number.")

                # Compare the original value with its cent-rounded value.
                #
                # If rounding changes the value, it contains fractional cents:
                #     Decimal("42.501") -> rejected
                #     Decimal("42.50")  -> accepted
                #
                # Trailing zeros do not change the numeric value:
                #     Decimal("42.500") -> accepted
                #
                # This validates the value without replacing it with a
                # rounded amount.
                if amount != amount.quantize(Decimal("0.01")):
                    raise ValueError(
                        "Amount must have no more than two decimal places."
                    )

                # Every check passed. Store the cleaned identifiers and
                # converted date and amount in the accepted list.
                transactions.append({
                    "transaction_id": transaction_id,
                    "customer_id": customer_id,
                    "merchant_name": merchant_name,
                    "transaction_date": transaction_date,
                    "amount": amount,
                })

                # Reserve this ID after accepting the record.
                # Later records with the same ID will be rejected.
                seen_ids.add(transaction_id)

            except (ValueError, InvalidOperation) as error:

                # Capture expected validation and conversion failures.
                #
                # The rejected record is not added to transactions.
                # Processing continues with the next CSV record.
                rejected_rows.append({
                    "row_number": row_number,
                    "reason": str(error),
                })

    # Return both lists as a tuple.
    #
    # The caller can unpack them:
    #     transactions, rejected_rows = load_transactions(csv_path)
    return transactions, rejected_rows