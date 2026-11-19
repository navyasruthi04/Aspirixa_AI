"""Saves and reads a student's topic mastery (the BKT results)."""
from datetime import datetime, timezone

from database.models import TopicMastery
from services.bkt import classify_topic


def clamp_mastery(value, default=0.5):
    """Keeps a mastery value between 0 and 1. Missing value -> default."""
    if value is None:
        return default
    return min(max(float(value), 0.0), 1.0)


def save_topic_mastery(db, user_id, topic, mastery, source, subject=None):
    """Creates or updates the mastery row. The caller commits."""
    row = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user_id, TopicMastery.topic == topic)
        .first()
    )

    if row is None:
        row = TopicMastery(user_id=user_id, topic=topic)
        db.add(row)

    row.mastery = float(mastery)
    row.status = classify_topic(row.mastery)
    row.source = source
    if subject:
        row.subject = subject
    row.updated_at = datetime.now(timezone.utc)

    return row


def get_mastery_map(db, user_id):
    """{topic: mastery} for this student."""
    rows = db.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
    return {row.topic: row.mastery for row in rows}


def get_weak_topics(db, user_id):
    """Topic names whose saved status is Weak, weakest first."""
    rows = (
        db.query(TopicMastery)
        .filter(TopicMastery.user_id == user_id, TopicMastery.status == "Weak")
        .order_by(TopicMastery.mastery, TopicMastery.topic)
        .all()
    )
    return [row.topic for row in rows]
