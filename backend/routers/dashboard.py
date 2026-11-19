from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import Student, User
from routers.auth import get_current_user
from services.dashboard import build_dashboard


router = APIRouter(
    prefix="/api",
    tags=["Dashboard"]
)


@router.get("/dashboard")
def get_dashboard(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """Home dashboard: stats, top recommendation, today's plan, achievements."""

    student = (
        db.query(Student)
        .filter(Student.user_id == user.id)
        .order_by(Student.id.desc())
        .first()
    )

    return build_dashboard(db, user, student)
