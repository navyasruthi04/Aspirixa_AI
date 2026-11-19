from fastapi import APIRouter, Depends
from pydantic import BaseModel

from database.models import User
from routers.auth import get_current_user
from services.recommender import recommend


router = APIRouter(
    prefix="/recommendation",
    tags=["Recommendation"]
)


class RecommendationRequest(BaseModel):
    qualification: str
    preparation_level: str
    study_hours: float
    subject_preferences: str | None = None
    # Optional extras. When they are sent, eligibility also checks age
    # and TOPSIS also uses the preferred field / target exam.
    age: int | None = None
    field: str | None = None
    target_exam: str | None = None


@router.post("")
def get_recommendation(
    request: RecommendationRequest,
    user: User = Depends(get_current_user)
):
    """
    Eligibility filtering -> XGBoost suitability -> TOPSIS ranking
    -> SHAP explanation (see services/recommender.py).

    If the student is not eligible for any exam, the list of
    recommendations is empty and "eligibility" says why.
    """

    return recommend(
        qualification=request.qualification,
        preparation_level=request.preparation_level,
        study_hours=request.study_hours,
        subject_preferences=request.subject_preferences,
        age=request.age,
        field=request.field,
        target_exam=request.target_exam,
    )
