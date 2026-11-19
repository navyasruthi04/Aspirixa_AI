from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database.connection import get_db
from services.ssc_service import list_exams, get_exam, get_calendar


# Exam information is public, read-only data, so no login is needed here.
router = APIRouter(
    prefix="/ssc",
    tags=["SSC Examinations"]
)


@router.get("/exams")
def exams(db: Session = Depends(get_db)):
    return list_exams(db)


@router.get("/exams/{code}")
def exam_detail(code: str, db: Session = Depends(get_db)):
    exam = get_exam(db, code)

    if exam is None:
        raise HTTPException(status_code=404, detail="Examination not found.")

    return exam


@router.get("/calendar")
def calendar(db: Session = Depends(get_db)):
    return get_calendar(db)
