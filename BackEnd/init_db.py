"""Create missing database tables and verify connectivity."""

from sqlalchemy import text

from database import Base, engine

# Import the model so its table is registered in Base.metadata.
from models import Transaction  # noqa: F401


def main() -> None:
    # Execute a simple query to verify the database connection.
    with engine.connect() as connection:
        database_name = connection.execute(
            text("SELECT current_database()")
        ).scalar_one()

        print(f"Connected to database: {database_name}")

    # Create tables that do not exist yet.
    # This does not migrate or alter existing table definitions.
    Base.metadata.create_all(bind=engine)

    print("Transactions table is ready.")


if __name__ == "__main__":
    main()