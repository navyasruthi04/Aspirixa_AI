from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import DiagnosticResult, QuizAttempt, TopicMastery, User
from routers.auth import get_current_user


router = APIRouter(
    prefix="/progress",
    tags=["Progress"]
)


def _iso(value):
    return value.isoformat() if value else None


@router.get("/summary")
def progress_summary(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Everything saved for this student, in one response."""

    topics = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user.id)
        .order_by(TopicMastery.mastery, TopicMastery.topic)
        .all()
    )

    latest = (
        db.query(DiagnosticResult)
        .filter(DiagnosticResult.user_id == user.id)
        .order_by(DiagnosticResult.id.desc())
        .first()
    )

    attempts = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id)
        .count()
    )

    correct = (
        db.query(QuizAttempt)
        .filter(QuizAttempt.user_id == user.id, QuizAttempt.correct.is_(True))
        .count()
    )

    return {
        "diagnostic": None if latest is None else {
            "total_answered": latest.total_answered,
            "correct_answers": latest.correct_answers,
            "score_percentage": latest.score_percentage,
            "taken_at": _iso(latest.created_at)
        },
        "topics": [
            {
                "topic": row.topic,
                "subject": row.subject,
                "mastery": row.mastery,
                "status": row.status,
                "source": row.source,
                "updated_at": _iso(row.updated_at)
            }
            for row in topics
        ],
        "weak_topics": [row.topic for row in topics if row.status == "Weak"],
        "quiz": {
            "attempts": attempts,
            "correct": correct,
            "accuracy": round(correct * 100 / attempts, 1) if attempts else 0
        }
    }
