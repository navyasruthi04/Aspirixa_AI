from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from routers.auth import get_current_user
from services import dates
from services.plan_builder import build_user_plan
from services.study_log import set_session_status


router = APIRouter(
    prefix="/study-plan",
    tags=["Study Plan"]
)


class StudyPlanRequest(BaseModel):
    study_hours: float
    # None = use the weak topics saved from the student's diagnostic/quiz.
    # A list (even an empty one) = use exactly that list.
    weak_topics: list[str] | None = None
    preparation_level: str = "beginner"


class SessionStatusRequest(BaseModel):
    session_id: str
    completed: bool
    topic: str | None = None
    minutes: int = 0
    syllabus_key: str | None = None


@router.post("")
def generate_study_plan(
    request: StudyPlanRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Constraint-based plan: weak topics + available hours + syllabus
    still to cover + revision (see services/study_planner.py).
    """

    return build_user_plan(
        db,
        user_id=user.id,
        study_hours=request.study_hours,
        preparation_level=request.preparation_level,
        weak_topics=request.weak_topics,
    )


@router.put("/session")
def update_session_status(
    request: SessionStatusRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Ticks / unticks a session of today's plan (saved for the dashboard)."""

    set_session_status(
        db,
        user_id=user.id,
        day=dates.today(),
        session_key=request.session_id,
        topic=request.topic,
        minutes=request.minutes,
        completed=request.completed,
        syllabus_key=request.syllabus_key,
    )

    db.commit()

    return {
        "session_id": request.session_id,
        "completed": request.completed,
    }
