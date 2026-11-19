"""Builds today's study plan for one student from what is saved in the database."""
from database.models import Student, TopicMastery, StudySession
from services import dates
from services.study_log import completed_keys, exam_code_for, pending_syllabus_topics
from services.study_planner import create_study_plan


def build_user_plan(db, user_id, study_hours, preparation_level, weak_topics=None):
    """
    weak_topics=None  -> use the weak topics saved from diagnostic / quiz.
    weak_topics=[...] -> use exactly this list of topic names.
    """

    rows = db.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
    by_topic = {row.topic: row for row in rows}

    if weak_topics is None:
        weak = [
            {"topic": row.topic, "subject": row.subject, "mastery": row.mastery}
            for row in rows if row.status == "Weak"
        ]
    else:
        weak = [
            {
                "topic": name,
                "subject": by_topic[name].subject if name in by_topic else None,
                "mastery": by_topic[name].mastery if name in by_topic else None,
            }
            for name in weak_topics
        ]

    # Syllabus of the student's target exam (SSC exams have a syllabus)
    student = (
        db.query(Student)
        .filter(Student.user_id == user_id)
        .order_by(Student.id.desc())
        .first()
    )

    code = exam_code_for(student.target_exam if student else None) or "CGL"

    new_topics = pending_syllabus_topics(
        db, user_id, code, weak_subjects=[w["subject"] for w in weak]
    )

    revision_topics = [
        row.topic for row in rows if row.status in ("Developing", "Mastered")
    ]

    plan = create_study_plan(
        study_hours=study_hours,
        weak_topics=weak,
        preparation_level=preparation_level,
        new_topics=new_topics,
        revision_topics=revision_topics,
    )

    # Show what the student already ticked today
    today = dates.today()
    done = completed_keys(db, user_id, today)

    # Keep sessions completed today visible, even if the syllabus
    # planner has moved on to the next topic.
    saved_sessions = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.plan_date == today,
            StudySession.completed.is_(True),
        )
        .order_by(StudySession.id)
        .all()
    )

    existing_ids = {s["id"] for s in plan.get("sessions", [])}

    completed_sessions = []

    for row in saved_sessions:
        if row.session_key not in existing_ids:
            session_type = row.session_key.split(":", 1)[0]

            completed_sessions.append({
                "type": session_type,
                "topic": row.topic,
                "subject": "Completed",
                "minutes": row.minutes,
                "priority": "Medium",
                "weak": False,
                "resource": "Previously completed today.",
                "time": "—",
                "period": "",
                "id": row.session_key,
                "status": "completed",
            })

    plan["sessions"] = completed_sessions + plan.get("sessions", [])

    first_open_marked = False

    for session in plan.get("sessions", []):
        if session["id"] in done:
            session["status"] = "completed"
        elif not first_open_marked:
            session["status"] = "current"
            first_open_marked = True
        else:
            session["status"] = "upcoming"

    plan["weak_topics"] = [w["topic"] for w in weak]
    plan["exam_code"] = code
    plan["plan_date"] = today.isoformat()

    return plan
