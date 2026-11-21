import os
import asyncio
import json
from contextlib import asynccontextmanager

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from database.connection import get_db, SessionLocal
from database.init_db import init_database
from database.models import Student, User
from database.schemas import StudentCreate, StudentResponse
from routers.recommendation import router as recommendation_router
from routers.diagnostic import router as diagnostic_router
from routers.study_plan import router as study_plan_router
from routers.quiz import router as quiz_router
from routers.auth import router as auth_router, get_current_user
from routers.ssc import router as ssc_router
from routers.ssc_sync import router as ssc_sync_router
from routers.syllabus import router as syllabus_router
from routers.progress import router as progress_router
from routers.dashboard import router as dashboard_router
from routers.feedback import router as feedback_router
from services.ssc_scheduler import sync_loop, sync_enabled
from services.analytics import build_analytics
from services.ssc_seed import seed_ssc
from services.syllabus_seed import seed_syllabus


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Runs once when the server starts:
    # create missing tables/columns, then load the SSC starting data.
    init_database()

    db = SessionLocal()
    try:
        seed_ssc(db)
        seed_syllabus(db)   # Phase 4: SSC syllabus (safe to run every start)
    finally:
        db.close()

    # Load (or train, the first time) the XGBoost exam-suitability model
    # so the first recommendation request is not slow.
    try:
        from ml.xgboost_model import ensure_model
        ensure_model()
    except Exception as error:
        print(f"WARNING: exam model could not be loaded: {error}")

    # Phase 3: official SSC notice sync every 6 hours (set ASPIRIXA_SYNC=off to disable)
    task = asyncio.create_task(sync_loop()) if sync_enabled() else None

    yield

    if task:
        task.cancel()


app = FastAPI(
    title="Aspirixa AI API",
    description="AI-based Government Exam Selection and Adaptive Preparation System",
    version="1.2.0",
    lifespan=lifespan
)


# Allow React frontend to communicate with FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        origin.strip()
        for origin in os.getenv(
            "CORS_ORIGINS",
            "http://localhost:5173,http://127.0.0.1:5173"
        ).split(",")
        if origin.strip()
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(recommendation_router)
app.include_router(diagnostic_router)
app.include_router(study_plan_router)
app.include_router(quiz_router)
app.include_router(auth_router)
app.include_router(ssc_router)
app.include_router(ssc_sync_router)
app.include_router(syllabus_router)
app.include_router(progress_router)
app.include_router(dashboard_router)
app.include_router(feedback_router)

@app.get("/")
def home():
    return {
        "message": "Welcome to Aspirixa AI API",
        "status": "Backend is running"
    }


@app.post("/students", response_model=StudentResponse)
def create_student(
    student: StudentCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    new_student = Student(
        user_id=user.id,
        name=student.name,
        qualification=student.qualification,
        age=student.age,
        target_exam=student.target_exam,
        preparation_level=student.preparation_level,
        study_hours=student.study_hours,
        interested_field=student.interested_field,
        subject_preferences=student.subject_preferences,
        learning_preferences=student.learning_preferences
    )

    db.add(new_student)
    db.commit()
    db.refresh(new_student)

    return new_student


@app.get("/students")
def get_students(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Each student only sees their own records
    return db.query(Student).filter(Student.user_id == user.id).all()

@app.get("/api/analytics")
def get_analytics(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    # Built from this student's saved diagnostic, mastery and quiz results
    return build_analytics(db, user.id)


def _student_for(db: Session, user: User):
    return (
        db.query(Student)
        .filter(Student.user_id == user.id)
        .order_by(Student.id.desc())
        .first()
    )


def _profile_response(student: Student):
    try:
        prefs = json.loads(student.learning_preferences or "{}")
    except json.JSONDecodeError:
        prefs = {}

    return {
        "id": student.id,
        "fullName": student.name,
        "qualification": student.qualification,
        "age": student.age or 18,
        "targetExam": student.target_exam or "Not selected",
        "level": student.preparation_level,
        "dailyHours": student.study_hours,
        "field": student.interested_field or "General",
        "subjects": [
            subject.strip()
            for subject in (student.subject_preferences or "").split(",")
            if subject.strip()
        ],
        "prefs": prefs
    }


@app.get("/api/profile")
def get_profile(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    student = _student_for(db, user)

    if not student:
        return {
            "fullName": user.full_name,
            "qualification": "",
            "age": 18,
            "targetExam": "SSC CGL",
            "level": "Beginner",
            "dailyHours": 2,
            "field": "General",
            "subjects": [],
            "prefs": {
                "dailyReminders": True,
                "adaptiveDifficulty": True,
                "weakTopicPriority": True,
                "revisionReminders": True
            }
        }

    return _profile_response(student)


@app.put("/api/profile")
def update_profile(
    profile: dict,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user)
):
    student = _student_for(db, user)

    if not student:
        student = Student(
            user_id=user.id,
            name=user.full_name,
            qualification="",
            preparation_level="Beginner",
            study_hours=0
        )
        db.add(student)

    # Only fields that were sent are changed. (Before, sending just
    # {"prefs": ...} would also erase the saved subjects.)
    if "fullName" in profile:
        student.name = profile["fullName"]
    if "qualification" in profile:
        student.qualification = profile["qualification"]
    if "age" in profile:
        student.age = profile["age"]
    if "targetExam" in profile:
        student.target_exam = profile["targetExam"]
    if "level" in profile:
        student.preparation_level = profile["level"]
    if "dailyHours" in profile:
        student.study_hours = profile["dailyHours"]
    if "field" in profile:
        student.interested_field = profile["field"]
    if "subjects" in profile:
        student.subject_preferences = ", ".join(profile["subjects"])
    if "prefs" in profile:
        student.learning_preferences = json.dumps(profile["prefs"])

    db.commit()
    db.refresh(student)

    return _profile_response(student)
