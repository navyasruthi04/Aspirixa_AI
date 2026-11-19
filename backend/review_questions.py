
"""
Review questions by hand. Run from the backend folder.

    python review_questions.py summary
    python review_questions.py list --status draft
    python review_questions.py list --status draft --diagnostic
    python review_questions.py show 12
    python review_questions.py review 12 --reviewer "Your Name"
    python review_questions.py review-diagnostic --reviewer "Your Name"
    python review_questions.py edit 12 --explanation "..." --difficulty Medium --tiers CGL,CHSL
    python review_questions.py unreview 12

Review commands never mark a question reviewed automatically.
You must independently solve each question and enter your answer.
"""
import argparse

from database.connection import SessionLocal
from database.init_db import init_database
from services import question_review as qr

DIAGNOSTIC_TARGET = 24


def _print_questions(rows):
    for q in rows:
        print(
            f"{q.id:>5}  [{q.status:<8}] "
            f"{q.subject:<34} {q.topic:<22} "
            f"{q.difficulty:<6} {q.question[:60]}"
        )
    print(f"\n{len(rows)} question(s)")


def _display_question(q):
    print("\n" + "=" * 75)
    print(f"Question {q.id} | {q.subject} / {q.topic} / {q.difficulty}")
    print("=" * 75)
    print(q.question)

    for letter in "abcd":
        print(f"  {letter.upper()}) {getattr(q, 'option_' + letter)}")


def _review_diagnostic(db, reviewer):
    questions = qr.list_questions(
        db,
        status="draft",
        diagnostic_only=True,
    )

    if not questions:
        print("There are no draft diagnostic questions remaining.")
        return

    print(f"\nDiagnostic batch review")
    print(f"Reviewer: {reviewer}")
    print(f"Questions awaiting review: {len(questions)}")
    print("\nInstructions:")
    print("- Solve each question independently.")
    print("- Enter A, B, C, or D to submit your answer.")
    print("- Enter S to skip a question.")
    print("- Enter Q to stop the session.")
    print("- The stored answer key will not be displayed.")

    reviewed = 0
    skipped = 0
    failed = 0

    for q in questions:
        _display_question(q)

        answer = input(
            "\nYour answer (A/B/C/D, S=skip, Q=quit): "
        ).strip().upper()

        if answer == "Q":
            print("\nBatch review stopped by reviewer.")
            break

        if answer == "S":
            skipped += 1
            print(f"Question {q.id} skipped.")
            continue

        if answer not in ("A", "B", "C", "D"):
            failed += 1
            print("Invalid input. Question left as DRAFT.")
            continue

        try:
            qr.mark_reviewed(
                db,
                q.id,
                reviewer,
                answer,
                allow_missing_explanation=False,
            )
            reviewed += 1
            print(f"Question {q.id} successfully marked REVIEWED.")

        except qr.ReviewError as error:
            failed += 1
            print(f"Question {q.id} NOT reviewed: {error}")

    print("\n" + "=" * 75)
    print("BATCH REVIEW RESULTS")
    print("=" * 75)
    print(f"Successfully reviewed: {reviewed}")
    print(f"Skipped:               {skipped}")
    print(f"Not reviewed:          {failed}")
    print("\nRun 'python review_questions.py summary' to verify progress.")


def _review_diagnostic_batch(db, reviewer, answers_text=None):
    questions = qr.list_questions(db, status="draft")

    if not questions:
        print("No draft diagnostic questions remaining.")
        return

    print(f"\nQuestions to review: {len(questions)}")
    print("Solve each question independently.\n")

    for index, q in enumerate(questions, start=1):
        print("\n" + "=" * 70)
        print(f"{index}. Question ID: {q.id} | {q.subject} | {q.topic}")
        print(q.question)

        for letter in "abcd":
            print(f"  {letter.upper()}) {getattr(q, 'option_' + letter)}")

    if answers_text is None:
        answers_text = input(
            "\nEnter answers in order, separated by commas (A,B,C,...).\n"
            "Use S to skip a question:\n> "
        )

    answers = [
        answer.strip().upper()
        for answer in answers_text.replace(",", " ").split()
    ]

    if len(answers) != len(questions):
        print(
            f"Not done: Expected {len(questions)} answers, "
            f"but received {len(answers)}. No questions were changed."
        )
        return

    if any(answer not in ("A", "B", "C", "D", "S") for answer in answers):
        print("Not done: Use only A, B, C, D or S. No questions were changed.")
        return

    reviewed = 0
    incorrect = 0
    skipped = 0

    for q, answer in zip(questions, answers):
        if answer == "S":
            skipped += 1
            print(f"Question {q.id}: skipped")
            continue

        try:
            qr.mark_reviewed(
                db,
                q.id,
                reviewer,
                answer,
                allow_missing_explanation=False,
            )
            reviewed += 1
            print(f"Question {q.id}: REVIEWED")

        except qr.ReviewError as error:
            incorrect += 1
            print(f"Question {q.id}: NOT REVIEWED - {error}")

    print("\n" + "=" * 70)
    print("BATCH REVIEW SUMMARY")
    print(f"Successfully reviewed: {reviewed}")
    print(f"Incorrect/not approved: {incorrect}")
    print(f"Skipped: {skipped}")
    print("=" * 70)


def run(args, db):
    if args.command == "summary":
        s = qr.summary(db)
        print(f"Draft: {s['draft']}   Reviewed: {s['reviewed']}")
        print(
            f"Diagnostic questions reviewed: "
            f"{s['diagnostic_reviewed']} of {s['diagnostic_total']}"
        )

        if s["diagnostic_reviewed"] < DIAGNOSTIC_TARGET:
            print(
                f"WARNING: fewer than {DIAGNOSTIC_TARGET} reviewed "
                "diagnostic questions - the pilot diagnostic "
                "would be shorter than planned."
            )
        return

    if args.command == "list":
        _print_questions(
            qr.list_questions(
                db,
                args.status,
                args.subject,
                args.topic,
                args.diagnostic,
            )
        )
        return

    if args.command == "show":
        print(qr.describe(qr._get(db, args.id)))
        return
    if args.command == "review-diagnostic-batch":
        _review_diagnostic_batch(db, args.reviewer, args.answers)
        return
    if args.command == "review-diagnostic":
        _review_diagnostic(db, args.reviewer)
        return

    if args.command == "review":
        q = qr._get(db, args.id)
        print(
            f"Question {q.id} | "
            f"{q.subject} / {q.topic} / {q.difficulty}\n"
        )
        print(q.question)

        for letter in "abcd":
            print(
                f"  {letter.upper()}) "
                f"{getattr(q, 'option_' + letter)}"
            )

        print(f"\nExplanation: {q.explanation or '(none)'}\n")

        answer = input(
            "Solve it yourself, then type the answer letter (A/B/C/D): "
        )

        qr.mark_reviewed(
            db,
            args.id,
            args.reviewer,
            answer,
            args.allow_missing_explanation,
        )

        print(f"Question {args.id} marked REVIEWED by {args.reviewer}.")
        return

    if args.command == "edit":
        qr.edit_question(
            db,
            args.id,
            explanation=args.explanation,
            difficulty=args.difficulty,
            subject=args.subject,
            topic=args.topic,
            correct_answer=args.answer,
            source=args.source,
            tiers=args.tiers.split(",") if args.tiers is not None else None,
        )
        print(
            f"Question {args.id} updated. "
            "It is now DRAFT again (version raised); review it again."
        )
        return

    if args.command == "unreview":
        qr.unreview(db, args.id)
        print(f"Question {args.id} is DRAFT again.")


def main():
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )

    sub = parser.add_subparsers(dest="command", required=True)

    sub.add_parser("summary")

    p = sub.add_parser("list")
    p.add_argument("--status", choices=["draft", "reviewed"])
    p.add_argument("--subject")
    p.add_argument("--topic")
    p.add_argument("--diagnostic", action="store_true")

    p = sub.add_parser("show")
    p.add_argument("id", type=int)

    p = sub.add_parser("review")
    p.add_argument("id", type=int)
    p.add_argument("--reviewer", required=True)
    p.add_argument("--allow-missing-explanation", action="store_true")

    p = sub.add_parser("review-diagnostic")
    p.add_argument("--reviewer", required=True)
    
    p = sub.add_parser("review-diagnostic-batch")
    p.add_argument("--reviewer", required=True)
    p.add_argument("--answers")

    p = sub.add_parser("edit")
    p.add_argument("id", type=int)
    p.add_argument("--explanation")
    p.add_argument("--difficulty")
    p.add_argument("--subject")
    p.add_argument("--topic")
    p.add_argument("--answer")
    p.add_argument("--source")
    p.add_argument(
        "--tiers",
        help="comma list, e.g. CGL,CHSL (empty string clears)",
    )

    p = sub.add_parser("unreview")
    p.add_argument("id", type=int)

    args = parser.parse_args()

    init_database()
    db = SessionLocal()

    try:
        run(args, db)
    except qr.ReviewError as error:
        print(f"Not done: {error}")
        raise SystemExit(1)
    finally:
        db.close()


if __name__ == "__main__":
    main()
