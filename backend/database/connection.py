
import os
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase

BASE_DIR = Path(__file__).resolve().parents[2]

# Render supplies DATABASE_URL; local development defaults to SQLite.
DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL:
    # Use the psycopg 3 driver for PostgreSQL.
    if DATABASE_URL.startswith("postgres://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgres://", "postgresql+psycopg://", 1
        )
    elif DATABASE_URL.startswith("postgresql://"):
        DATABASE_URL = DATABASE_URL.replace(
            "postgresql://", "postgresql+psycopg://", 1
        )

    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,
    )
else:
    DATABASE_PATH = BASE_DIR / "database" / "aspirixa.db"
    DATABASE_PATH.parent.mkdir(parents=True, exist_ok=True)

    DATABASE_URL = f"sqlite:///{DATABASE_PATH}"

    engine = create_engine(
        DATABASE_URL,
        connect_args={"check_same_thread": False},
    )

SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine,
)


class Base(DeclarativeBase):
    pass


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
