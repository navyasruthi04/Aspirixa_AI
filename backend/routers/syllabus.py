from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import SyllabusTopic, SyllabusProgress, User
from routers.auth import get_current_user
from services.syllabus_data import OFFICIAL_SOURCES, EXAM_NAMES

router = APIRouter(prefix="/syllabus", tags=["Syllabus"])


class ProgressBody(BaseModel):
    completed: bool


def _topic_dict(topic, completed):
    return {
        "id": topic.id, "key": topic.key, "exam_code": topic.exam_code,
        "tier": topic.tier, "subject": topic.subject, "area": topic.area,
        "subject_note": topic.subject_note, "topic": topic.topic,
        "subtopics": topic.subtopics or [], "sort_order": topic.sort_order,
        "completed": completed,
    }


@router.get("/exams")
def syllabus_exams(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    rows = db.query(SyllabusTopic.exam_code).distinct().order_by(SyllabusTopic.exam_code).all()
    order = list(EXAM_NAMES)
    codes = sorted((row[0] for row in rows), key=lambda c: order.index(c) if c in order else len(order))
    return [{"code": c, "name": EXAM_NAMES.get(c, f"SSC {c}")} for c in codes]


@router.get("")
def get_syllabus(
    exam_code: str = Query("CGL", min_length=2, max_length=20),
    tier: str | None = Query(None, max_length=40),
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    exam_code = exam_code.upper()
    query = db.query(SyllabusTopic).filter(SyllabusTopic.exam_code == exam_code)
    if tier:
        query = query.filter(SyllabusTopic.tier == tier)
    topics = query.order_by(SyllabusTopic.id).all()
    if not topics:
        raise HTTPException(404, "No syllabus found for this exam/tier.")
    topic_ids = [t.id for t in topics]
    completed_ids = {
        row.topic_id for row in db.query(SyllabusProgress.topic_id).filter(
            SyllabusProgress.user_id == user.id,
            SyllabusProgress.topic_id.in_(topic_ids),
        ).all()
    }
    grouped = {}
    for topic in topics:
        item = _topic_dict(topic, topic.id in completed_ids)
        grouped.setdefault(topic.tier, {}).setdefault(topic.subject, []).append(item)
    tiers = []
    for tier_name, subjects in grouped.items():
        subject_rows = []
        for subject_name, items in subjects.items():
            subject_rows.append({
                "name": subject_name,
                "note": items[0]["subject_note"],
                "topics": items,
                "completed": sum(1 for x in items if x["completed"]),
                "total": len(items),
            })
        tiers.append({"name": tier_name, "subjects": subject_rows})
    total = len(topics)
    completed = len(completed_ids)
    return {
        "exam_code": exam_code, "tiers": tiers,
        "progress": {"completed": completed, "total": total,
                     "percentage": round(completed * 100 / total) if total else 0},
        "source_urls": [
            url for url in (
                OFFICIAL_SOURCES.get(exam_code),
                "https://ssc.gov.in/for-candidates/syllabus",
                "https://ssc.gov.in/home/notice-board",
            ) if url
        ],
        "disclaimer": "Topic breakdown is a study guide based on SSC notice syllabus headings. Always verify the latest official notice and corrigenda.",
    }


@router.put("/progress/{topic_key}")
def update_progress(
    topic_key: str, body: ProgressBody,
    db: Session = Depends(get_db), user: User = Depends(get_current_user),
):
    topic = db.query(SyllabusTopic).filter(SyllabusTopic.key == topic_key).first()
    if topic is None:
        raise HTTPException(404, "Syllabus topic not found.")
    progress = db.query(SyllabusProgress).filter(
        SyllabusProgress.user_id == user.id,
        SyllabusProgress.topic_id == topic.id,
    ).first()
    if body.completed and progress is None:
        db.add(SyllabusProgress(user_id=user.id, topic_id=topic.id,
                                completed_at=datetime.now(timezone.utc)))
    elif not body.completed and progress is not None:
        db.delete(progress)
    db.commit()
    return {"topic_key": topic_key, "completed": body.completed}
