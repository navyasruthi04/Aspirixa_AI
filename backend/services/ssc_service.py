"""Reads SSC exam data from the database and shapes it for the frontend."""
from datetime import date

from database.models import SSCExam, SSCNotification

DISCLAIMER = (
    "Always confirm important dates on the official SSC website (ssc.gov.in) "
    "before you apply or travel for an exam."
)

VERIFICATION_TEXT = {
    "official": "Read from the official SSC website",
    "secondary": "Reported by other websites. Not yet checked against ssc.gov.in",
}

# (field on the notification, label shown in the calendar)
CALENDAR_FIELDS = [
    ("notification_date", "Notification published", "notification"),
    ("apply_start", "Applications open", "application"),
    ("apply_end", "Last date to apply", "application"),
    ("fee_last_date", "Last date for fee payment", "application"),
    ("correction_start", "Correction window opens", "application"),
    ("correction_end", "Correction window closes", "application"),
    ("tier1_start", "Tier 1 exam starts", "exam"),
    ("tier1_end", "Tier 1 exam window ends", "exam"),
]


def _iso(value):
    return value.isoformat() if value else None


def application_status(n, today):
    if n.apply_start and today < n.apply_start:
        return "upcoming"
    if n.apply_end:
        return "open" if today <= n.apply_end else "closed"
    return "unknown"


def exam_stage(n, today):
    if not n.tier1_start:
        return "not_announced"
    if today < n.tier1_start:
        return "upcoming"
    if n.tier1_end and today > n.tier1_end:
        return "completed"
    return "ongoing"


def _pretty(d):
    return f"{d.day} {d.strftime('%B %Y')}" if d else None


def status_label(n, today):
    """One short sentence that tells the student where this exam stands."""
    app = application_status(n, today)
    stage = exam_stage(n, today)

    if app == "upcoming":
        return "Applications open soon", "blue"
    if app == "open":
        return "Applications open", "green"
    if stage == "ongoing":
        return "Tier 1 exam in progress", "amber"
    if stage == "upcoming":
        days = (n.tier1_start - today).days
        return f"Applications closed. Tier 1 starts in {days} days", "primary"
    if stage == "completed":
        return "Tier 1 exam window over. Result awaited", "gray"
    return "Latest notification available", "gray"


def serialize_notification(n, today):
    label, tone = status_label(n, today)
    return {
        "ref": n.notification_ref,
        "title": n.title,
        "status": label,
        "status_tone": tone,
        "application_status": application_status(n, today),
        "exam_stage": exam_stage(n, today),
        "dates": {
            "notification_date": _iso(n.notification_date),
            "apply_start": _iso(n.apply_start),
            "apply_end": _iso(n.apply_end),
            "fee_last_date": _iso(n.fee_last_date),
            "correction_start": _iso(n.correction_start),
            "correction_end": _iso(n.correction_end),
            "exam_notice_date": _iso(n.exam_notice_date),
            "tier1_start": _iso(n.tier1_start),
            "tier1_end": _iso(n.tier1_end),
        },
        "tier2_info": n.tier2_info,
        "vacancies": n.vacancies,
        "vacancy_note": n.vacancy_note,
        "fee_text": n.fee_text,
        "eligibility_note": n.eligibility_note,
        "admit_card_info": n.admit_card_info,
        "result_info": n.result_info,
        "notice_pdf_url": n.notice_pdf_url,
        "apply_url": n.apply_url,
        "source": {
            "name": n.source_name,
            "url": n.source_url,
            "all": n.sources or [],
            "verification": n.verification,
            "verification_text": VERIFICATION_TEXT.get(n.verification, n.verification),
            "last_verified": _iso(n.last_verified),
        },
        "discrepancies": n.discrepancies or [],
    }


def serialize_exam(exam, today):
    notifications = [serialize_notification(n, today) for n in exam.notifications]
    return {
        "code": exam.code,
        "name": exam.name,
        "full_name": exam.full_name,
        "description": exam.description,
        "data_status": exam.data_status,
        "qualification": exam.qualification,
        "age_limit": exam.age_limit,
        "age_relaxation": exam.age_relaxation,
        "pattern": exam.pattern,
        "official_url": exam.official_url,
        "last_verified": _iso(exam.last_verified),
        "latest_notification": notifications[0] if notifications else None,
        "notifications": notifications,
    }


def list_exams(db, today=None):
    today = today or date.today()
    exams = db.query(SSCExam).order_by(SSCExam.id).all()
    # Exams with details first, pending ones after
    exams.sort(key=lambda e: (e.data_status != "available", e.id))
    return {
        "official_site": "https://ssc.gov.in/",
        "disclaimer": DISCLAIMER,
        "exams": [serialize_exam(e, today) for e in exams],
    }


def get_exam(db, code, today=None):
    today = today or date.today()
    exam = db.query(SSCExam).filter(SSCExam.code == code.upper()).first()
    return serialize_exam(exam, today) if exam else None


def get_calendar(db, today=None):
    """All important dates of every exam's latest notification, oldest first."""
    today = today or date.today()
    events = []

    for exam in db.query(SSCExam).all():
        if not exam.notifications:
            continue
        latest = exam.notifications[0]

        for field, label, kind in CALENDAR_FIELDS:
            value = getattr(latest, field)
            if value:
                events.append({
                    "date": value.isoformat(),
                    "exam_code": exam.code,
                    "exam_name": exam.name,
                    "label": label,
                    "kind": kind,
                    "is_past": value < today,
                })

    events.sort(key=lambda e: (e["date"], e["exam_name"]))
    return {"today": today.isoformat(), "disclaimer": DISCLAIMER, "events": events}
