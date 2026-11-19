"""
Human review of questions (Step 1). The logic lives here so it can be tested;
review_questions.py is the command-line wrapper around it.

A question becomes 'reviewed' ONLY through mark_reviewed(), which needs
  - a reviewer name,
  - the answer letter the reviewer worked out themselves (must match the key),
  - an explanation (unless the reviewer explicitly allows a missing one).
Editing a reviewed question puts it back to 'draft' and raises its version.
"""
from datetime import datetime, timezone

from sqlalchemy import func

from database.models import Question, QuestionTier
from services.question_validation import (
    ANSWERS, DIFFICULTIES, EXAM_TIERS, SUBJECTS, normalise_subject,
)


class ReviewError(Exception):
    pass


def _get(db, question_id):
    q = db.query(Question).filter(Question.id == question_id).first()
    if q is None:
        raise ReviewError(f"Question {question_id} not found.")
    return q


def list_questions(db, status=None, subject=None, topic=None, diagnostic_only=False):
    query = db.query(Question)
    if status:
        query = query.filter(Question.status == status)
    if subject:
        query = query.filter(Question.subject == normalise_subject(subject))
    if topic:
        query = query.filter(Question.topic == topic)
    if diagnostic_only:
        query = query.filter(Question.is_diagnostic.is_(True))
    return query.order_by(Question.id).all()


def summary(db):
    """Counts for the pilot-readiness check."""
    by_status = dict(
        db.query(Question.status, func.count(Question.id)).group_by(Question.status).all()
    )
    diag_total = db.query(func.count(Question.id)).filter(Question.is_diagnostic.is_(True)).scalar()
    diag_reviewed = (
        db.query(func.count(Question.id))
        .filter(Question.is_diagnostic.is_(True), Question.status == "reviewed")
        .scalar()
    )
    return {
        "draft": by_status.get("draft", 0),
        "reviewed": by_status.get("reviewed", 0),
        "diagnostic_total": diag_total,
        "diagnostic_reviewed": diag_reviewed,
    }


def describe(q):
    """Plain-text view of one question for the reviewer."""
    tiers = ", ".join(sorted(t.tier for t in q.tiers)) or "(none assigned)"
    lines = [
        f"Question {q.id}   [{q.status}]  version {q.version}",
        f"Subject: {q.subject}   Topic: {q.topic}   Difficulty: {q.difficulty}",
        f"Exam tiers: {tiers}   Source: {q.source}   Diagnostic: {'yes' if q.is_diagnostic else 'no'}",
        "",
        q.question,
        f"  A) {q.option_a}",
        f"  B) {q.option_b}",
        f"  C) {q.option_c}",
        f"  D) {q.option_d}",
        "",
        f"Answer key : {q.correct_answer}",
        f"Explanation: {q.explanation or '(none)'}",
    ]
    if q.status == "reviewed":
        lines.append(f"Reviewed by {q.reviewed_by} on {q.reviewed_at}")
    return "\n".join(lines)


def mark_reviewed(db, question_id, reviewer, confirmed_answer, allow_missing_explanation=False):
    """
    The reviewer solved the question themselves and typed the letter they got.
    Only if it matches the key (and the other checks pass) the question becomes 'reviewed'.
    """
    q = _get(db, question_id)

    reviewer = (reviewer or "").strip()
    if not reviewer:
        raise ReviewError("A reviewer name is required.")

    confirmed = (confirmed_answer or "").strip().upper()
    if confirmed not in ANSWERS:
        raise ReviewError("Enter the answer letter you worked out: A, B, C or D.")
    if confirmed != q.correct_answer:
        raise ReviewError(
            f"Your answer {confirmed} does not match the key {q.correct_answer}. "
            "Not marked as reviewed. Fix the key (edit) or check your working."
        )

    if not (q.explanation or "").strip() and not allow_missing_explanation:
        raise ReviewError("This question has no explanation. Add one (edit --explanation) before review.")

    q.status = "reviewed"
    q.reviewed_by = reviewer
    q.reviewed_at = datetime.now(timezone.utc)
    db.commit()
    return q


def unreview(db, question_id):
    q = _get(db, question_id)
    q.status = "draft"
    q.reviewed_by = None
    q.reviewed_at = None
    db.commit()
    return q


def edit_question(db, question_id, **fields):
    """
    Allowed fields: explanation, difficulty, subject, topic, correct_answer,
    source, is_diagnostic, tiers (list), question, option_a..option_d.
    Any change puts the question back to 'draft' and raises its version.
    """
    q = _get(db, question_id)
    changed = False

    for name, value in fields.items():
        if value is None:
            continue

        if name == "tiers":
            tiers = [t.strip().upper() for t in value if t.strip()]
            bad = [t for t in tiers if t not in EXAM_TIERS]
            if bad:
                raise ReviewError(f"Unknown tier(s) {bad}; allowed: {EXAM_TIERS}")
            q.tiers = [QuestionTier(tier=t) for t in sorted(set(tiers))]
        elif name == "difficulty":
            value = value.strip().capitalize()
            if value not in DIFFICULTIES:
                raise ReviewError("Difficulty must be Easy, Medium or Hard.")
            q.difficulty = value
        elif name == "subject":
            value = normalise_subject(value)
            if value not in SUBJECTS:
                raise ReviewError(f"Subject must be one of {SUBJECTS}.")
            q.subject = value
        elif name == "correct_answer":
            value = value.strip().upper()
            if value not in ANSWERS:
                raise ReviewError("Answer must be A, B, C or D.")
            q.correct_answer = value
        elif name in ("explanation", "topic", "source", "question",
                      "option_a", "option_b", "option_c", "option_d"):
            value = value.strip()
            if not value and name != "explanation":
                raise ReviewError(f"{name} cannot be empty.")
            setattr(q, name, value or None)
        elif name == "is_diagnostic":
            q.is_diagnostic = bool(value)
        else:
            raise ReviewError(f"Cannot edit field '{name}'.")
        changed = True

    if changed:
        q.version += 1
        q.status = "draft"
        q.reviewed_by = None
        q.reviewed_at = None
        db.commit()

    return q
