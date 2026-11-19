from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import QuizAttempt, User
from routers.auth import get_current_user
from services.adaptive_quiz import (
    choose_topic,
    get_next_question,
    process_answer
)
from services.progress import (
    clamp_mastery,
    get_mastery_map,
    save_topic_mastery
)
from services.question_bank import get_question


router = APIRouter(
    prefix="/quiz",
    tags=["Adaptive Quiz"]
)


class NextQuestionRequest(BaseModel):
    # Both are optional now. Without a topic, the server picks the
    # student's weakest topic using the mastery saved in the database.
    topic: str | None = None
    mastery_probability: float | None = None
    answered_question_ids: list[int] = Field(
        default_factory=list
    )


class QuizAnswerRequest(BaseModel):
    question_id: int
    answer: str
    # Only used if this topic has no saved mastery yet
    mastery_probability: float | None = None


@router.post("/next")
def next_question(
    request: NextQuestionRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    saved = get_mastery_map(db, user.id)

    if request.topic:
        topic = request.topic
        mastery = saved.get(
            topic,
            clamp_mastery(request.mastery_probability)
        )
    else:
        topic, mastery = choose_topic(
            saved,
            request.answered_question_ids
        )

    question = None

    if topic is not None:
        question = get_next_question(
            topic=topic,
            mastery=mastery,
            answered_question_ids=request.answered_question_ids
        )

    if not question:
        raise HTTPException(
            status_code=404,
            detail="No more questions available."
        )

    return question


@router.post("/answer")
def submit_answer(
    request: QuizAnswerRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    question = get_question(request.question_id)

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found."
        )

    topic = question["topic"]

    correct = (
        request.answer.upper()
        == question["correct_answer"].upper()
    )

    # The mastery saved on the server is the source of truth
    saved = get_mastery_map(db, user.id)
    mastery = saved.get(
        topic,
        clamp_mastery(request.mastery_probability)
    )

    result = process_answer(
        mastery=mastery,
        correct=correct,
        difficulty=question["difficulty"]
    )

    db.add(QuizAttempt(
        user_id=user.id,
        question_id=request.question_id,
        topic=topic,
        difficulty=question["difficulty"],
        correct=correct,
        mastery_before=result["previous_mastery"],
        mastery_after=result["updated_mastery"]
    ))

    save_topic_mastery(
        db,
        user_id=user.id,
        topic=topic,
        mastery=result["updated_mastery"],
        source="quiz",
        subject=question["subject"]
    )

    db.commit()

    return {
        "question_id": request.question_id,
        "topic": topic,
        "correct": correct,
        "correct_answer": question["correct_answer"],
        **result
    }
