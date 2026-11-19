"""
Phase 3 tests: polite client, parser and sync job.
Run from the backend folder:   python -m unittest test_phase3 -v

A small fake SSC server runs on your own computer, so the real HTTP code
(retries, blocking, redirects, robots.txt) is exercised without touching ssc.gov.in.
NOTE: the JSON shape used here is an ASSUMPTION until you run probe_ssc.py.
"""
import json
import os
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

from services import ssc_client, ssc_parser
from services.ssc_client import SSCClient, SyncError, BlockedError

STATE = {"mode": "ok", "hits": 0, "robots": "User-agent: *\nAllow: /"}

NOTICES = {"data": [
    {"id": 101, "headline": "Combined Graduate Level Examination, 2026: Notice of Examination",
     "examId": 7, "redirectUrl": "cgl2026.pdf", "createdAt": "2026-05-21T10:00:00.000Z",
     "startDate": "2026-05-22", "endDate": "2026-06-22"},
    {"id": 102, "headline": "Notice: Office closed on holiday", "examId": None,
     "redirectUrl": None, "createdAt": "2026-10-01T10:00:00.000Z"},
    {"id": 103, "headline": "Combined Higher Secondary Level Examination, 2026",
     "redirectUrl": "https://evil.example.com/x.pdf", "createdAt": "2026-09-07T00:00:00Z"},
]}


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *a):
        pass

    def _send(self, code, body=b"", ctype="application/json", headers=None):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        for k, v in (headers or {}).items():
            self.send_header(k, v)
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        STATE["hits"] += 1
        if self.path.startswith("/robots.txt"):
            return self._send(200, STATE["robots"].encode(), "text/plain")
        if self.path.startswith("/api/list"):
            m = STATE["mode"]
            if m == "forbidden":
                return self._send(403, b"{}")
            if m == "flaky" and STATE["hits"] < 4:
                return self._send(500, b"{}")
            if m == "redirect":
                return self._send(302, b"", headers={"Location": "https://evil.example.com/a"})
            if m == "badjson":
                return self._send(200, b"<html>not json</html>", "text/html")
            return self._send(200, json.dumps(NOTICES).encode())
        if self.path.startswith("/file.pdf"):
            return self._send(200, b"%PDF-1.4 fake", "application/pdf")
        if self.path.startswith("/notpdf"):
            return self._send(200, b"hello", "application/pdf")
        self._send(404)


def make_client():
    return SSCClient(delay=0, backoff=0.01, base_url=BASE, retries=3)


try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.connection import Base
    from database import models  # noqa: F401
    from database.models import SSCNotice, SyncLog
    from services import ssc_sync
    HAVE_DB = True
except ImportError:          # lets the client/parser tests run without SQLAlchemy
    HAVE_DB = False


def make_session():
    h, path = tempfile.mkstemp(suffix=".db"); os.close(h)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)()


class ClientTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        global BASE
        cls.server = HTTPServer(("127.0.0.1", 0), Handler)
        BASE = f"http://127.0.0.1:{cls.server.server_port}"
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()

    def setUp(self):
        STATE.update(mode="ok", hits=0, robots="User-agent: *\nAllow: /")

    def test_gets_json(self):
        data = make_client().get_json(f"{BASE}/api/list")
        self.assertEqual(len(data["data"]), 3)

    def test_retries_then_succeeds(self):
        STATE["mode"] = "flaky"
        data = make_client().get_json(f"{BASE}/api/list")
        self.assertIn("data", data)

    def test_gives_up_after_retries(self):
        STATE["mode"] = "flaky"
        STATE["hits"] = -100
        with self.assertRaises(SyncError):
            make_client().get_json(f"{BASE}/api/list")

    def test_403_stops_without_retrying(self):
        STATE["mode"] = "forbidden"
        with self.assertRaises(BlockedError):
            make_client().get_json(f"{BASE}/api/list")
        self.assertLessEqual(STATE["hits"], 2)       # robots.txt + one request

    def test_robots_disallow_respected(self):
        STATE["robots"] = "User-agent: *\nDisallow: /api/"
        with self.assertRaises(BlockedError):
            make_client().get_json(f"{BASE}/api/list")

    def test_redirect_to_other_host_refused(self):
        STATE["mode"] = "redirect"
        c = make_client()
        c.base_url = ssc_client.BASE_URL      # behave like the real client for host checks
        c.check_robots = False
        with self.assertRaises(BlockedError):
            c.get_json(f"{BASE}/api/list")

    def test_other_hosts_refused(self):
        c = SSCClient(delay=0, check_robots=False)
        with self.assertRaises(BlockedError):
            c.get_json("https://evil.example.com/data")
        with self.assertRaises(BlockedError):
            c.get_json("http://ssc.gov.in/plain-http")

    def test_bad_json_is_clear_error(self):
        STATE["mode"] = "badjson"
        with self.assertRaises(SyncError):
            make_client().get_json(f"{BASE}/api/list")

    def test_pdf_download_and_validation(self):
        self.assertTrue(make_client().get_pdf(f"{BASE}/file.pdf").startswith(b"%PDF"))
        with self.assertRaises(SyncError):
            make_client().get_pdf(f"{BASE}/notpdf")


class ParserTests(unittest.TestCase):
    def test_list_shapes(self):
        item = {"headline": "x"}
        for payload in ([item], {"data": [item]}, {"data": {"rows": [item]}},
                        {"result": {"items": [item]}}):
            self.assertEqual(len(ssc_parser.extract_items(payload)), 1)
        self.assertEqual(ssc_parser.extract_items({"data": []}), [])
        self.assertEqual(ssc_parser.extract_items("oops"), [])

    def test_dates(self):
        p = ssc_parser.parse_date
        self.assertEqual(p("2026-05-21T10:00:00.000Z").isoformat(), "2026-05-21")
        self.assertEqual(p("22-06-2026").isoformat(), "2026-06-22")
        self.assertEqual(p("22nd June, 2026").isoformat(), "2026-06-22")
        self.assertIsNone(p("31-02-2026"))
        self.assertIsNone(p("01-01-1990"))
        self.assertIsNone(p("garbage"))
        self.assertIsNone(p(None))

    def test_attachment_urls(self):
        b = ssc_parser.build_attachment_url
        self.assertTrue(b("a.pdf").startswith("https://ssc.gov.in/api/attachment/"))
        self.assertIsNone(b("https://evil.example.com/a.pdf"))
        self.assertIsNone(b("javascript:alert(1)"))
        self.assertIsNone(b(None))

    def test_classify(self):
        c = ssc_parser.classify_exam
        self.assertEqual(c("Combined Graduate Level Examination, 2026"), "CGL")
        self.assertEqual(c("Combined Higher Secondary Level Exam"), "CHSL")
        self.assertEqual(c("Multi Tasking (Non-Technical) Staff"), "MTS")
        self.assertEqual(c("Junior Engineer (Civil) 2026"), "JE")
        self.assertIsNone(c("Holiday notice"))

    def test_facts_clear_case(self):
        text = ("Date of commencement of submission of online application: 22-05-2026\n"
                "Last date and time for receipt of online application: 22-06-2026\n"
                "Tentative 12,256 vacancies. Fee Rs. 100/- for others.")
        facts, notes = ssc_parser.extract_facts(text)
        self.assertEqual(facts["apply_start"], "2026-05-22")
        self.assertEqual(facts["apply_end"], "2026-06-22")
        self.assertEqual(facts["vacancies"], 12256)
        self.assertIn(100, facts["fee_amounts_seen"])

    def test_facts_ambiguous_left_out(self):
        facts, notes = ssc_parser.extract_facts("1,200 vacancies in A and 3,400 vacancies in B")
        self.assertNotIn("vacancies", facts)
        self.assertTrue(notes)

    def test_facts_bad_order_dropped(self):
        text = ("commencement of submission of application 30-06-2026\n"
                "last date for submission of application 01-06-2026")
        facts, notes = ssc_parser.extract_facts(text)
        self.assertNotIn("apply_end", facts)
        self.assertTrue(notes)

    def test_facts_empty(self):
        self.assertEqual(ssc_parser.extract_facts("")[0], {})


@unittest.skipUnless(HAVE_DB, 'SQLAlchemy not installed here')
class SyncTests(unittest.TestCase):
    def setUp(self):
        self.db = make_session()
        self._orig = ssc_sync.pdf_to_text
        ssc_sync.pdf_to_text = lambda data: ("last date for submission of application 22-06-2026 "
                                              "12,256 vacancies")

    def tearDown(self):
        ssc_sync.pdf_to_text = self._orig

    class FakeClient:
        def __init__(self, payload=None, error=None):
            self.payload, self.error, self.pdf_calls = payload, error, 0
        def get_json(self, url, params=None):
            if self.error:
                raise self.error
            return self.payload if params["page"] == 1 else {"data": []}
        def get_pdf(self, url):
            self.pdf_calls += 1
            return b"%PDF-fake"

    def test_first_sync_saves_and_reads_pdf(self):
        c = self.FakeClient(NOTICES)
        log = ssc_sync.run_sync(self.db, client=c)
        self.assertIn(log.status, ("success", "partial"))
        self.assertEqual(log.new_count, 3)
        n = self.db.query(SSCNotice).filter_by(uid="101").one()
        self.assertEqual(n.exam_code, "CGL")
        self.assertEqual(n.pdf_status, "extracted")
        self.assertEqual(n.extracted["facts"]["vacancies"], 12256)
        # untrusted PDF host was dropped, not downloaded
        self.assertIsNone(self.db.query(SSCNotice).filter_by(uid="103").one().attachment_url)
        self.assertEqual(c.pdf_calls, 1)

    def test_no_duplicates_on_second_run(self):
        c = self.FakeClient(NOTICES)
        ssc_sync.run_sync(self.db, client=c)
        log2 = ssc_sync.run_sync(self.db, client=c)
        self.assertEqual(log2.new_count, 0)
        self.assertEqual(self.db.query(SSCNotice).count(), 3)
        self.assertEqual(c.pdf_calls, 1)             # PDF not re-downloaded

    def test_blocked_is_logged_not_crashed(self):
        log = ssc_sync.run_sync(self.db, client=self.FakeClient(error=BlockedError("403")))
        self.assertEqual(log.status, "blocked")

    def test_network_failure_is_logged(self):
        log = ssc_sync.run_sync(self.db, client=self.FakeClient(error=SyncError("down")))
        self.assertEqual(log.status, "failed")
        self.assertEqual(self.db.query(SyncLog).count(), 1)

    def test_unknown_shape_reported(self):
        log = ssc_sync.run_sync(self.db, client=self.FakeClient({"weird": 1}))
        self.assertEqual(log.status, "partial")
        self.assertIn("unknown shape", log.message)

    def test_manual_pdf_rules(self):
        with self.assertRaises(ValueError):
            ssc_sync.process_manual_pdf(self.db, "https://evil.example.com/a.pdf", client=self.FakeClient())
        with self.assertRaises(ValueError):
            ssc_sync.process_manual_pdf(self.db, "https://ssc.gov.in/page.html", client=self.FakeClient())
        n = ssc_sync.process_manual_pdf(
            self.db, "https://ssc.gov.in/api/attachment/uploads/masterData/NoticeBoards/CGL_2026.pdf",
            client=self.FakeClient())
        self.assertEqual(n.pdf_status, "extracted")
        self.assertEqual(n.exam_code, "CGL")


if __name__ == "__main__":
    unittest.main()
