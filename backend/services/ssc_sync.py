"""
Official SSC notice sync. Runs from a scheduled job, never per user request.

Safety rules:
  * a notice is saved once (unique uid), later runs only update it
  * values read from PDFs are stored on the notice and COMPARED with the
    curated exam data; curated data is never overwritten automatically
  * a block from the site stops the run; nothing tries to work around it
"""
import threading
from datetime import datetime, timezone

from sqlalchemy.orm import Session

from database.models import SSCNotice, SSCNotification, SyncLog
from services.ssc_client import (
    SSCClient, SyncError, BlockedError, NOTICE_API, is_allowed_url, BASE_URL,
)
from services.ssc_parser import (
    extract_items, normalize_item, pdf_to_text, extract_facts, classify_exam,
)

_lock = threading.Lock()

# Exams for which we read PDFs (others are listed but not parsed)
PDF_EXAMS = {"CGL", "CHSL", "MTS", "GD", "CPO", "JE", "STENO", "SELECTION_POST", "JHT"}


def _now():
    return datetime.now(timezone.utc)


def _compare_with_curated(db, exam_code, facts):
    """Returns plain-text differences between PDF facts and our saved record."""
    if not exam_code or not facts:
        return []
    saved = (db.query(SSCNotification)
             .filter(SSCNotification.exam_code == exam_code)
             .order_by(SSCNotification.notification_date.desc()).first())
    if not saved:
        return []
    diffs = []
    if facts.get("apply_end") and saved.apply_end \
            and facts["apply_end"] != saved.apply_end.isoformat():
        diffs.append(f"Last date: PDF {facts['apply_end']}, app {saved.apply_end.isoformat()}")
    if facts.get("vacancies") and saved.vacancies and facts["vacancies"] != saved.vacancies:
        diffs.append(f"Vacancies: PDF {facts['vacancies']}, app {saved.vacancies}")
    return diffs


def _process_pdf(db, client, notice):
    try:
        text = pdf_to_text(client.get_pdf(notice.attachment_url))
    except BlockedError:
        raise
    except RuntimeError as exc:                       # PDF library missing
        notice.pdf_status, notice.extract_note = "unavailable", str(exc)
        return False
    except SyncError as exc:
        notice.pdf_status, notice.extract_note = "failed", str(exc)
        return False
    except Exception as exc:                          # unreadable / corrupt PDF
        notice.pdf_status, notice.extract_note = "failed", f"Could not read PDF: {exc.__class__.__name__}"
        return False

    facts, notes = extract_facts(text)
    diffs = _compare_with_curated(db, notice.exam_code, facts)
    notice.extracted = {"facts": facts, "differs_from_app": diffs}
    notice.extract_note = "; ".join(notes) or None
    notice.pdf_status = "extracted"
    return True


def run_sync(db: Session, trigger="scheduled", client=None, pages=2, limit=10,
             max_pdfs=5, params_extra=None):
    """Runs one sync. Returns the SyncLog row."""
    log = SyncLog(trigger=trigger, status="failed")
    db.add(log); db.commit()

    if not _lock.acquire(blocking=False):
        log.message, log.finished_at = "Another sync is already running.", _now()
        db.commit()
        return log

    client = client or SSCClient()
    new = updated = pdfs = fetched = 0
    problems = []

    try:
        for page in range(1, pages + 1):
            params = {
                "page": page, "limit": limit, "contentType": "notice-boards",
                "key": "createdAt", "order": "DESC", "isAttachment": "true",
                "language": "english",
                "attributes": "id,headline,examId,contentType,redirectUrl,"
                              "startDate,endDate,language,createdAt",
            }
            params.update(params_extra or {})
            items = extract_items(client.get_json(NOTICE_API, params=params))
            if not items:
                if page == 1:
                    problems.append("The notice list came back empty or in an unknown shape.")
                break

            for raw in items:
                fetched += 1
                data = normalize_item(raw)
                if data is None:
                    problems.append("Skipped one item with no headline/id.")
                    continue

                notice = db.query(SSCNotice).filter(SSCNotice.uid == data["uid"]).first()
                is_new = notice is None
                if is_new:
                    notice = SSCNotice(uid=data["uid"], pdf_status="none")
                    db.add(notice)
                    new += 1
                else:
                    changed = any(getattr(notice, k) != v for k, v in data.items() if k != "uid")
                    updated += 1 if changed else 0

                for key, value in data.items():
                    setattr(notice, key, value)
                notice.source_url = data["attachment_url"] or BASE_URL

                if notice.attachment_url and notice.pdf_status == "none":
                    notice.pdf_status = "pending"

                if (notice.pdf_status == "pending" and pdfs < max_pdfs
                        and notice.exam_code in PDF_EXAMS):
                    if _process_pdf(db, client, notice):
                        pdfs += 1
                db.commit()

        log.status = "partial" if problems else "success"
    except BlockedError as exc:
        db.rollback()
        log.status, problems = "blocked", [str(exc)]
    except SyncError as exc:
        db.rollback()
        log.status, problems = "failed", [str(exc)]
    except Exception as exc:                         # never crash the server
        db.rollback()
        log.status, problems = "failed", [f"Unexpected error: {exc.__class__.__name__}: {exc}"]
    finally:
        _lock.release()

    log.fetched, log.new_count, log.updated_count, log.pdf_count = fetched, new, updated, pdfs
    log.message = "; ".join(problems) or None
    log.finished_at = _now()
    db.commit()
    return log


def process_manual_pdf(db: Session, url: str, client=None):
    """Fallback: the person pastes an official PDF link and we process it."""
    if not is_allowed_url(url) or not url.lower().split("?")[0].endswith(".pdf"):
        raise ValueError("Please paste a https://ssc.gov.in/... link that ends with .pdf")

    client = client or SSCClient()
    uid = f"pdf:{url}"
    notice = db.query(SSCNotice).filter(SSCNotice.uid == uid).first()
    if notice is None:
        name = url.rsplit("/", 1)[-1]
        notice = SSCNotice(uid=uid, headline=f"Manually added: {name}",
                           attachment_url=url, source_url=url,
                           exam_code=classify_exam(name), pdf_status="pending")
        db.add(notice)

    ok = _process_pdf(db, client, notice)
    db.commit()
    db.add(SyncLog(trigger="manual_pdf", status="success" if ok else "failed",
                   pdf_count=1 if ok else 0, finished_at=_now(),
                   message=notice.extract_note, fetched=1,
                   new_count=0))
    db.commit()
    return notice


def serialize_notice(n: SSCNotice):
    return {
        "id": n.id, "headline": n.headline, "exam_code": n.exam_code,
        "published_on": n.published_on.isoformat() if n.published_on else None,
        "start_date": n.start_date.isoformat() if n.start_date else None,
        "end_date": n.end_date.isoformat() if n.end_date else None,
        "pdf_url": n.attachment_url, "pdf_status": n.pdf_status,
        "extracted": n.extracted, "note": n.extract_note,
        "first_seen_at": n.first_seen_at.isoformat() if n.first_seen_at else None,
    }


def serialize_log(l: SyncLog):
    return {
        "id": l.id, "trigger": l.trigger, "status": l.status,
        "started_at": l.started_at.isoformat() if l.started_at else None,
        "finished_at": l.finished_at.isoformat() if l.finished_at else None,
        "fetched": l.fetched, "new": l.new_count, "updated": l.updated_count,
        "pdfs_read": l.pdf_count, "message": l.message,
    }
