from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from routers.auth import get_current_user
from services.feedback import build_feedback_for_user


router = APIRouter(
    prefix="/feedback",
    tags=["Explainable AI & Feedback"]
)


@router.get("")
def get_feedback(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    """
    Module 6: why the exam was recommended (SHAP reasons), the most
    important contributing factors and the next steps for this student.
    """

    return build_feedback_for_user(db, user.id)
