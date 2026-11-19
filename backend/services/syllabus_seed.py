"""Idempotently load the built-in SSC syllabus without resetting student progress."""
from database.models import SyllabusTopic
from services.syllabus_data import SYLLABUS


def seed_syllabus(db):
    added = updated = 0
    for item in SYLLABUS:
        row = db.query(SyllabusTopic).filter(SyllabusTopic.key == item["key"]).first()
        if row is None:
            db.add(SyllabusTopic(**item))
            added += 1
        else:
            for field, value in item.items():
                setattr(row, field, value)
            updated += 1
    db.commit()
    return {"topics_added": added, "topics_updated": updated, "total": len(SYLLABUS)}
