"""
Loads question rows into the `questions` table (Step 1).

RULES
- Rows are checked first (services/question_validation.py). Bad rows are refused
  and listed in a report. Good rows are still imported unless strict=True.
- EVERY imported question starts as status = 'draft'. Nothing is 'reviewed'
  until a person marks it with review_questions.py.
- Safe to run again: rows already in the database with the same content are
  skipped; rows whose id exists with different content are refused (never overwritten).
"""
import csv
from pathlib import Path

from sqlalchemy import text

from database.models import Question, QuestionTier
from services.question_validation import duplicate_key, validate_rows, format_report

DEFAULT_SOURCE = "seed-csv-unverified"


def read_csv(path):
    with open(path, mode="r", encoding="utf-8-sig", newline="") as file:
        return list(csv.DictReader(file))


def _existing(db):
    keys, ids = {}, set()
    for q in db.query(Question).all():
        ids.add(q.id)
        keys[duplicate_key(q.question, [q.option_a, q.option_b, q.option_c, q.option_d])] = q.id
    return keys, ids


def import_rows(db, rows, source=DEFAULT_SOURCE, strict=False):
    """
    Returns {"imported": n, "rejected": [...], "unchanged": [...], "report": text}.
    `source` is stored on every NEW question (unless the row has its own 'source' column).
    """
    keys, ids = _existing(db)
    good, rejected, unchanged = validate_rows(rows, existing_keys=keys, existing_ids=ids)

    report = format_report(good, rejected, unchanged)

    if strict and rejected:
        return {"imported": 0, "rejected": rejected, "unchanged": unchanged,
                "report": report + "\nSTRICT mode: nothing was imported."}

    # a row's own 'source' column wins over the default
    row_source = {}
    for index, row in enumerate(rows):
        value = (row.get("source") or "").strip()
        if value and (row.get("question_id") or "").strip().isdigit():
            row_source[int(row["question_id"])] = value

    for clean in good:
        question = Question(
            id=clean["id"],
            subject=clean["subject"],
            topic=clean["topic"],
            difficulty=clean["difficulty"],
            question=clean["question"],
            option_a=clean["option_a"],
            option_b=clean["option_b"],
            option_c=clean["option_c"],
            option_d=clean["option_d"],
            correct_answer=clean["correct_answer"],
            explanation=clean["explanation"],
            source=row_source.get(clean["id"], source),
            status="draft",              # never 'reviewed' from an import
            version=1,
            is_diagnostic=clean["is_diagnostic"],
        )
        question.tiers = [QuestionTier(tier=t) for t in clean["tiers"]]
        db.add(question)

    db.flush()

    # PostgreSQL only: ids were given explicitly, so move the id counter past them.
    if good and db.bind is not None and db.bind.dialect.name == "postgresql":
        db.execute(text(
            "SELECT setval(pg_get_serial_sequence('questions', 'id'), "
            "(SELECT MAX(id) FROM questions))"
        ))

    db.commit()

    return {"imported": len(good), "rejected": rejected, "unchanged": unchanged, "report": report}


def import_csv(db, path, source=DEFAULT_SOURCE, strict=False):
    return import_rows(db, read_csv(Path(path)), source=source, strict=strict)
