"""Background loop inside the FastAPI process: runs the sync every 6 hours."""
import asyncio
import os

from database.connection import SessionLocal
from services.ssc_sync import run_sync

INTERVAL_SECONDS = 6 * 60 * 60
FIRST_RUN_DELAY = 30          # let the server finish starting first


def _run_once():
    db = SessionLocal()
    try:
        log = run_sync(db, trigger="scheduled")
        print(f"[ssc-sync] {log.status}: fetched={log.fetched} new={log.new_count} "
              f"pdfs={log.pdf_count} {log.message or ''}")
    finally:
        db.close()


async def sync_loop():
    await asyncio.sleep(FIRST_RUN_DELAY)
    while True:
        try:
            await asyncio.to_thread(_run_once)
        except Exception as exc:       # the loop must never die
            print(f"[ssc-sync] error: {exc}")
        await asyncio.sleep(INTERVAL_SECONDS)


def sync_enabled():
    return os.environ.get("ASPIRIXA_SYNC", "on").lower() != "off"
