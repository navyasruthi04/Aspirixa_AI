"""
Load Dataset/questions.csv (or another csv) into the questions table.

Run from the backend folder:
    python import_questions.py                       # seed file, source "seed-csv-unverified"
    python import_questions.py --source original-hand-built   # ONLY once the team confirms authorship
    python import_questions.py --csv path/to/batch.csv --report batch_report.txt
    python import_questions.py --strict               # refuse the whole file if any row is bad

All imported questions are 'draft'. Use review_questions.py to review them.
"""
import argparse
from pathlib import Path

from database.connection import SessionLocal, BASE_DIR
from database.init_db import init_database
from services.question_import import import_csv, DEFAULT_SOURCE


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--csv", default=str(BASE_DIR / "Dataset" / "questions.csv"))
    parser.add_argument("--source", default=DEFAULT_SOURCE,
                        help="where the questions came from (licence / authorship)")
    parser.add_argument("--report", help="also save the report to this file")
    parser.add_argument("--strict", action="store_true", help="import nothing if any row is bad")
    args = parser.parse_args()

    init_database()   # makes sure the tables exist

    db = SessionLocal()
    try:
        result = import_csv(db, args.csv, source=args.source, strict=args.strict)
    finally:
        db.close()

    print(result["report"])
    print(f"\nImported {result['imported']} new question(s) as DRAFT.")

    if args.report:
        Path(args.report).write_text(result["report"] + "\n", encoding="utf-8")
        print(f"Report saved to {args.report}")

    raise SystemExit(1 if result["rejected"] and args.strict else 0)


if __name__ == "__main__":
    main()
