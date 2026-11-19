"""Saves and reads the study sessions a student has completed."""
from datetime import datetime, timezone

def completed_keys(db, user_id, day):
    """Session keys already ticked by this student on this day."""
    from database.models import StudySession

    rows = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.plan_date == day,
            StudySession.completed.is_(True),
        )
        .all()
    )
    return {row.session_key for row in rows}


def set_session_status(db, user_id, day, session_key, topic, minutes, completed, syllabus_key=None):
    """Creates or updates the row. If the session was a syllabus topic, its
    syllabus progress is ticked / unticked too. The caller commits."""
    from database.models import StudySession, SyllabusProgress, SyllabusTopic

    row = (
        db.query(StudySession)
        .filter(
            StudySession.user_id == user_id,
            StudySession.plan_date == day,
            StudySession.session_key == session_key,
        )
        .first()
    )

    if row is None:
        row = StudySession(user_id=user_id, plan_date=day, session_key=session_key)
        db.add(row)

    row.topic = topic
    row.minutes = int(minutes or 0)
    row.completed = bool(completed)
    row.completed_at = datetime.now(timezone.utc) if completed else None

    if syllabus_key:
        topic_row = db.query(SyllabusTopic).filter(SyllabusTopic.key == syllabus_key).first()

        if topic_row is not None:
            progress = (
                db.query(SyllabusProgress)
                .filter(
                    SyllabusProgress.user_id == user_id,
                    SyllabusProgress.topic_id == topic_row.id,
                )
                .first()
            )

            if completed and progress is None:
                db.add(SyllabusProgress(
                    user_id=user_id,
                    topic_id=topic_row.id,
                    completed_at=datetime.now(timezone.utc),
                ))
            elif not completed and progress is not None:
                db.delete(progress)

    return row


def minutes_by_day(db, user_id):
    """{date: completed study minutes}"""
    from database.models import StudySession

    totals = {}

    rows = (
        db.query(StudySession)
        .filter(StudySession.user_id == user_id, StudySession.completed.is_(True))
        .all()
    )

    for row in rows:
        totals[row.plan_date] = totals.get(row.plan_date, 0) + (row.minutes or 0)

    return totals


# ----------------------------------------------------------------------
# Syllabus topics still to study (feeds the study planner)
# ----------------------------------------------------------------------
def exam_code_for(target_exam):
    """'SSC CGL' -> 'CGL'.  Anything that is not an SSC exam -> None."""
    words = (target_exam or "").upper().replace("-", " ").split()

    if len(words) >= 2 and words[0] == "SSC":
        return words[1]

    return None


def pending_syllabus_topics(db, user_id, exam_code, weak_subjects=()):
    """
    Syllabus topics of the first tier that the student has not completed,
    in syllabus order. Subjects that contain a weak topic come first.
    Returns [{"key", "topic", "subject"}].
    """
    from database.models import SyllabusProgress, SyllabusTopic

    if not exam_code:
        return []

    topics = (
        db.query(SyllabusTopic)
        .filter(SyllabusTopic.exam_code == exam_code)
        .order_by(SyllabusTopic.id)
        .all()
    )

    if not topics:
        return []

    first_tier = topics[0].tier
    topics = [t for t in topics if t.tier == first_tier]

    done = {
        row.topic_id
        for row in db.query(SyllabusProgress.topic_id).filter(SyllabusProgress.user_id == user_id).all()
    }

    pending = [t for t in topics if t.id not in done]

    # The question bank now says "General Intelligence & Reasoning" and
    # "English Language"; the syllabus says "General Intelligence and Reasoning",
    # "Reasoning and General Intelligence", "English Comprehension" ... To keep the
    # old matching exactly, the new labels are matched by the keyword the old
    # labels ("Reasoning", "English") used.
    match_word = {
        "general intelligence & reasoning": "reasoning",
        "english language": "english",
    }

    def _wanted_word(subject):
        lowered = subject.lower()
        return match_word.get(lowered, lowered)

    wanted = [_wanted_word(s) for s in weak_subjects if s]

    def priority(topic):
        subject = topic.subject.lower()
        return 0 if any(w in subject for w in wanted) else 1

    pending.sort(key=lambda t: (priority(t), t.id))

    return [{"key": t.key, "topic": t.topic, "subject": t.subject} for t in pending]
