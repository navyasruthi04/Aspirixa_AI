"""
Shared sync state and rules (no database imports, so it is easy to test).

* one lock, so only ONE sync can run at a time (scheduled or manual)
* pdf_decision(): says exactly why a notice's PDF is read or skipped
"""
import threading

_lock = threading.Lock()

# Exams whose PDFs are read (other notices are listed but not parsed)
PDF_EXAMS = {"CGL", "CHSL", "MTS", "GD", "CPO", "JE", "STENO", "SELECTION_POST", "JHT"}
MAX_PDF_ATTEMPTS = 3

SKIP_LABELS = {
    "no_attachment": "no PDF link",
    "not_tracked_exam": "not a tracked exam",
    "already_done": "already read",
    "too_many_failures": "failed 3 times",
    "limit_reached": "per-run limit",
}


class SyncBusyError(Exception):
    """A sync is already running."""


def is_sync_running():
    return _lock.locked()


def acquire():
    if not _lock.acquire(blocking=False):
        raise SyncBusyError("A sync is already running.")


def release():
    if _lock.locked():
        _lock.release()


def pdf_decision(exam_code, attachment_url, pdf_status, attempts, processed, max_pdfs):
    """Returns 'process', or the reason the PDF is skipped."""
    if not attachment_url:
        return "no_attachment"
    if pdf_status == "extracted":
        return "already_done"
    if exam_code not in PDF_EXAMS:
        return "not_tracked_exam"
    if (attempts or 0) >= MAX_PDF_ATTEMPTS:
        return "too_many_failures"
    if processed >= max_pdfs:
        return "limit_reached"
    return "process"
