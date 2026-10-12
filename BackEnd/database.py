"""
Configure the PostgreSQL connection and SQLAlchemy sessions.

Connection settings come from BackEnd/.env.
URL.create() handles passwords containing special characters.
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import URL, create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker


# Locate .env relative to this file, regardless of the working directory.
ENV_PATH = Path(__file__).resolve().parent / ".env"
load_dotenv(ENV_PATH)

# Fail early if a required connection setting is missing.
required_settings = (
    "DB_HOST",
    "DB_NAME",
    "DB_USER",
    "DB_PASSWORD",
)

missing_settings = [
    name for name in required_settings if not os.getenv(name)
]

if missing_settings:
    raise RuntimeError(
        f"Missing database settings: {', '.join(missing_settings)}"
    )

# Use the psycopg driver installed through requirements.txt.
DATABASE_URL = URL.create(
    drivername="postgresql+psycopg",
    username=os.environ["DB_USER"],
    password=os.environ["DB_PASSWORD"],
    host=os.environ["DB_HOST"],
    port=int(os.getenv("DB_PORT", "5432")),
    database=os.environ["DB_NAME"],
)

# The engine manages database connections.
# pool_pre_ping checks pooled connections before using them.
engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True,
)

# Each session represents a unit of database work.
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    """Base class shared by our SQLAlchemy models."""