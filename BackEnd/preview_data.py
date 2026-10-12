"""
Preview and validate the project's synthetic transaction CSV.

This script calls load_transactions(), which reads the CSV and returns:
    1. Accepted transactions containing validated, converted values.
    2. Rejected rows containing row numbers and reasons for rejection.

The script displays the accepted and rejected counts, followed by a
small sample of each result. It does not write to PostgreSQL or modify
the CSV file.

Expected project structure:
    retail-spending-insights/
        BackEnd/
            preview_data.py
            services/
                transactions.py
        data/
            synthetic_retail_transactions.csv

Run from the project root:
    python BackEnd/preview_data.py

Or run from the BackEnd folder:
    python preview_data.py
"""

# Path provides tools for building and working with filesystem paths.
# It handles path separators for the operating system automatically.
from pathlib import Path

# Import the function responsible for reading and validating CSV records.
# The services folder is alongside this script inside BackEnd.
from services.transactions import load_transactions


# Determine the project root using this script's location.
#
# __file__:
#     The path to this Python file.
#
# resolve():
#     Converts it to an absolute path and resolves symbolic links.
#
# First .parent:
#     Moves from preview_data.py to its containing folder, BackEnd.
#
# Second .parent:
#     Moves from BackEnd to the project root, retail-spending-insights.
#
# Using the script's location instead of the current working directory
# allows the data file to be found when running from either folder.
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Build the full path to the CSV file.
#
# With Path objects, "/" joins path components. It is not division.
# This creates a path; it does not open the file or verify that it exists.
CSV_PATH = PROJECT_ROOT / "data" / "synthetic_retail_transactions.csv"


def main() -> None:
    """
    Load transaction data and print a brief validation summary.

    Accepted transactions contain:
        - Transaction ID
        - Fictional customer ID
        - Merchant name
        - Transaction date as a Python date object
        - Amount as a Decimal value

    Rejected rows contain:
        - CSV row number
        - Reason the row failed validation

    Only the first three accepted records and first five rejected rows
    are displayed to keep terminal output manageable.

    Returns:
        None. Results are printed to the terminal.

    Raises:
        FileNotFoundError: If the CSV file cannot be found.
        ValueError: If required CSV columns are missing.
        OSError: If the file cannot be opened or read.
    """

    # Read and validate the CSV.
    #
    # load_transactions() returns two lists as a tuple.
    # Tuple unpacking assigns each list to its corresponding variable.
    transactions, rejected_rows = load_transactions(CSV_PATH)

    # Display the number of accepted and rejected rows.
    #
    # len() returns the number of items in each list.
    # The ":," format adds thousands separators, such as 5,000.
    print(f"Accepted: {len(transactions):,}")
    print(f"Rejected: {len(rejected_rows):,}")

    # "\n" inserts a blank line before the sample heading.
    print("\nFirst three transactions:")

    # [:3] selects up to the first three records.
    # If fewer than three records exist, it returns those available.
    # Each transaction is printed as a Python dictionary.
    for transaction in transactions[:3]:
        print(transaction)

    # An empty list is false in a conditional.
    # Display rejection details only when at least one row was rejected.
    if rejected_rows:
        print("\nFirst five rejected rows:")

        # Limit the rejection sample to five rows.
        # The full rejected_rows list remains available in memory.
        for rejected in rejected_rows[:5]:
            print(rejected)


# Run main() only when this file is executed directly.
#
# Direct execution:
#     python preview_data.py
#     Python sets __name__ to "__main__", so main() runs.
#
# Importing this file:
#     import preview_data
#     Python uses the module name, so main() does not run automatically.
if __name__ == "__main__":
    main()