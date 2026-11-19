from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import SSCNotice, SyncLog, User
from routers.auth import get_current_user
from services.ssc_sync import (
    run_sync, process_manual_pdf, serialize_notice, serialize_log,
)

router = APIRouter(prefix="/ssc", tags=["SSC Official Sync"])

MIN_MANUAL_GAP = timedelta(minutes=10)


class PdfRequest(BaseModel):
    url: str


@router.get("/notices")
def notices(exam: str | None = None, limit: int = 20, db: Session = Depends(get_db)):
    q = db.query(SSCNotice)
    if exam:
        q = q.filter(SSCNotice.exam_code == exam.upper())
    rows = (q.order_by(SSCNotice.published_on.desc().nullslast(), SSCNotice.id.desc())
            .limit(max(1, min(limit, 100))).all())
    return [serialize_notice(n) for n in rows]


@router.get("/sync/status")
def sync_status(db: Session = Depends(get_db)):
    last = db.query(SyncLog).order_by(SyncLog.id.desc()).first()
    last_ok = (db.query(SyncLog).filter(SyncLog.status.in_(["success", "partial"]))
               .order_by(SyncLog.id.desc()).first())
    return {
        "last_run": serialize_log(last) if last else None,
        "last_success_at": last_ok.finished_at.isoformat() if last_ok and last_ok.finished_at else None,
        "notice_count": db.query(SSCNotice).count(),
    }


@router.get("/sync/logs")
def sync_logs(limit: int = 20, db: Session = Depends(get_db)):
    rows = db.query(SyncLog).order_by(SyncLog.id.desc()).limit(max(1, min(limit, 100))).all()
    return [serialize_log(r) for r in rows]


@router.post("/sync/run")
def sync_now(db: Session = Depends(get_db), user: User = Depends(get_current_user)):
    # There is no admin role yet, so any signed-in user may trigger this,
    # but not more than once every 10 minutes (protects ssc.gov.in).
    last = db.query(SyncLog).filter(SyncLog.trigger == "manual").order_by(SyncLog.id.desc()).first()
    if last and last.started_at:
        started = last.started_at.replace(tzinfo=timezone.utc) if last.started_at.tzinfo is None else last.started_at
        if datetime.now(timezone.utc) - started < MIN_MANUAL_GAP:
            raise HTTPException(429, "A manual sync ran recently. Please wait a few minutes.")
    return serialize_log(run_sync(db, trigger="manual"))


@router.post("/sync/pdf")
def sync_pdf(body: PdfRequest, db: Session = Depends(get_db),
             user: User = Depends(get_current_user)):
    try:
        return serialize_notice(process_manual_pdf(db, body.url.strip()))
    except ValueError as exc:
        raise HTTPException(400, str(exc))
