"""
Test helper (Step 1): builds a temporary in-memory question bank from
Dataset/questions.csv, so tests do not depend on your real aspirixa.db.

TEST-ONLY: the seed questions are marked 'reviewed' here so the serving rule is
satisfied. The real database keeps them as 'draft' until a person reviews them.
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from database.connection import Base, BASE_DIR
from database import models  # noqa: F401  (registers the tables)
from services import question_bank
from services.question_import import import_csv


def make_session_factory():
    engine = create_engine(
        "sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool
    )
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine, autocommit=False, autoflush=False)


def use_seeded_test_bank():
    """Point question_bank at a fresh in-memory bank holding the 72 seed questions.
    Returns a function that undoes it (call it in tearDownModule)."""
    factory = make_session_factory()
    db = factory()
    try:
        result = import_csv(db, BASE_DIR / "Dataset" / "questions.csv")
        assert not result["rejected"], result["report"]
        db.query(models.Question).update({"status": "reviewed"})
        db.commit()
    finally:
        db.close()
    question_bank.set_session_factory(factory)
    return lambda: question_bank.set_session_factory(None)
