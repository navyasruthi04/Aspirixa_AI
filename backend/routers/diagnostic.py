from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import DiagnosticResult, User
from routers.auth import get_current_user
from services.diagnostic_analysis import analyse_answers, QuestionNotFound
from services.progress import save_topic_mastery
from services.question_bank import load_questions, load_diagnostic_questions


router = APIRouter(
    prefix="/diagnostic",
    tags=["Diagnostic"]
)


class Answer(BaseModel):
    question_id: int
    answer: str


class DiagnosticRequest(BaseModel):
    answers: list[Answer]


@router.get("/questions")
def get_questions(user: User = Depends(get_current_user)):

    questions = load_diagnostic_questions()

    # Don't send correct answers to the frontend
    safe_questions = []

    for question in questions:
        safe_questions.append({
            "question_id": int(question["question_id"]),
            "subject": question["subject"],
            "topic": question["topic"],
            "difficulty": question["difficulty"],
            "question": question["question"],
            "options": {
                "A": question["option_a"],
                "B": question["option_b"],
                "C": question["option_c"],
                "D": question["option_d"]
            }
        })

    return {
        "total_questions": len(safe_questions),
        "questions": safe_questions
    }


@router.post("/submit")
def submit_diagnostic(
    request: DiagnosticRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):

    question_map = {
        int(q["question_id"]): q
        for q in load_questions()
    }

    try:
        analysis = analyse_answers(
            [(a.question_id, a.answer) for a in request.answers],
            question_map
        )
    except QuestionNotFound as error:
        raise HTTPException(status_code=404, detail=str(error))

    topic_results = analysis["topic_results"]
    total_answered = analysis["answered"]
    correct_count = analysis["correct"]

    weak_topics = [
        result["topic"]
        for result in topic_results
        if result["status"] == "Weak"
    ]

    strong_topics = [
        result["topic"]
        for result in topic_results
        if result["status"] == "Mastered"
    ]

    score_percentage = round(
        (correct_count / total_answered) * 100,
        2
    ) if total_answered else 0

    overall_mastery = round(
        sum(r["mastery_probability"] for r in topic_results) * 100 / len(topic_results)
    ) if topic_results else 0

    # Save the result and each topic's mastery for this student.
    # A new diagnostic replaces the earlier mastery values (new baseline).
    if total_answered:
        for result in topic_results:
            save_topic_mastery(
                db,
                user_id=user.id,
                topic=result["topic"],
                mastery=result["mastery_probability"],
                source="diagnostic",
                subject=result["subject"]
            )

        db.add(DiagnosticResult(
            user_id=user.id,
            total_answered=total_answered,
            correct_answers=correct_count,
            score_percentage=score_percentage,
            topic_analysis=topic_results,
            weak_topics=weak_topics
        ))
        db.commit()

    return {
        "total_answered": total_answered,
        "correct_answers": correct_count,
        "score_percentage": score_percentage,
        "overall_mastery": overall_mastery,
        "topic_analysis": topic_results,
        "subject_analysis": analysis["subject_analysis"],
        "weak_topics": weak_topics,
        "strong_topics": strong_topics,
    }
