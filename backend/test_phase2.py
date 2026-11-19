"""
Phase 2 tests: accounts, login tokens, SSC data and database migration.

Run from the backend folder:
    python -m unittest test_phase2 -v

These tests use a temporary database, so your real aspirixa.db is not touched.
"""
import os
import tempfile
import time
import unittest
from datetime import date

from sqlalchemy import create_engine, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import sessionmaker

from database.connection import Base
from database import models, init_db
from database.models import User, Student, SSCExam, SSCNotification
from services import security, auth_service, ssc_service
from services.auth_service import AuthError
from services.ssc_seed import seed_ssc


def make_session():
    handle, path = tempfile.mkstemp(suffix=".db")
    os.close(handle)
    engine = create_engine(f"sqlite:///{path}")
    Base.metadata.create_all(engine)
    return sessionmaker(bind=engine)(), engine, path


class SecurityTests(unittest.TestCase):
    def test_password_hash_roundtrip(self):
        stored = security.hash_password("correct horse")
        self.assertNotIn("correct horse", stored)
        self.assertTrue(security.verify_password("correct horse", stored))
        self.assertFalse(security.verify_password("wrong", stored))

    def test_same_password_gives_different_hashes(self):
        self.assertNotEqual(security.hash_password("abc12345"), security.hash_password("abc12345"))

    def test_garbage_hash_is_rejected_not_crashing(self):
        self.assertFalse(security.verify_password("x", "not-a-hash"))

    def test_token_roundtrip(self):
        token = security.create_access_token(42)
        self.assertEqual(security.decode_access_token(token), 42)

    def test_tampered_token_rejected(self):
        header, payload, signature = security.create_access_token(1).split(".")
        forged_payload = security._b64url_encode(b'{"sub":"2","iat":1,"exp":9999999999}')
        self.assertIsNone(security.decode_access_token(f"{header}.{forged_payload}.{signature}"))

    def test_expired_token_rejected(self):
        token = security.create_access_token(1, lifetime_seconds=-10)
        self.assertIsNone(security.decode_access_token(token))

    def test_alg_none_token_rejected(self):
        header = security._b64url_encode(b'{"alg":"none","typ":"JWT"}')
        payload = security._b64url_encode(b'{"sub":"1","exp":9999999999}')
        self.assertIsNone(security.decode_access_token(f"{header}.{payload}."))

    def test_random_strings_rejected(self):
        for bad in ["", "abc", "a.b.c", "....", "a.b"]:
            self.assertIsNone(security.decode_access_token(bad))

    def test_secret_from_environment(self):
        os.environ["ASPIRIXA_SECRET_KEY"] = "test-secret"
        try:
            self.assertEqual(security.get_secret_key(), b"test-secret")
        finally:
            del os.environ["ASPIRIXA_SECRET_KEY"]


class AuthServiceTests(unittest.TestCase):
    def setUp(self):
        self.db, self.engine, self.path = make_session()
        auth_service.reset_login_guard()

    def tearDown(self):
        self.db.close(); self.engine.dispose(); os.remove(self.path)

    def test_register_and_login(self):
        result = auth_service.register_user(self.db, "Navya", "Navya@Example.com ", "password1")
        self.assertEqual(result["user"]["email"], "navya@example.com")
        self.assertEqual(security.decode_access_token(result["token"]), result["user"]["id"])

        logged_in = auth_service.login_user(self.db, "NAVYA@example.com", "password1")
        self.assertEqual(logged_in["user"]["id"], result["user"]["id"])

    def test_password_is_not_stored_in_plain_text(self):
        auth_service.register_user(self.db, "A", "a@b.co", "password1")
        self.assertNotIn("password1", self.db.query(User).one().password_hash)

    def test_duplicate_email_rejected(self):
        auth_service.register_user(self.db, "A", "a@b.co", "password1")
        with self.assertRaises(AuthError) as ctx:
            auth_service.register_user(self.db, "B", "A@B.co", "password2")
        self.assertEqual(ctx.exception.status_code, 409)

    def test_validation(self):
        cases = [("", "a@b.co", "password1"), ("A", "not-an-email", "password1"),
                 ("A", "a@b.co", "short"), ("A" * 81, "a@b.co", "password1"),
                 ("A", "a@b.co", "x" * 129)]
        for name, email, pw in cases:
            with self.assertRaises(AuthError) as ctx:
                auth_service.register_user(self.db, name, email, pw)
            self.assertEqual(ctx.exception.status_code, 422)

    def test_wrong_password_and_unknown_email_look_the_same(self):
        auth_service.register_user(self.db, "A", "a@b.co", "password1")
        with self.assertRaises(AuthError) as wrong:
            auth_service.login_user(self.db, "a@b.co", "badpassword")
        with self.assertRaises(AuthError) as unknown:
            auth_service.login_user(self.db, "nobody@b.co", "password1")
        self.assertEqual(wrong.exception.message, unknown.exception.message)
        self.assertEqual(wrong.exception.status_code, 401)

    def test_lockout_after_five_failures(self):
        auth_service.register_user(self.db, "A", "a@b.co", "password1")
        for _ in range(5):
            with self.assertRaises(AuthError):
                auth_service.login_user(self.db, "a@b.co", "badpassword")
        with self.assertRaises(AuthError) as ctx:
            auth_service.login_user(self.db, "a@b.co", "password1")  # even the right one
        self.assertEqual(ctx.exception.status_code, 429)

    def test_first_account_claims_old_unowned_profile_only(self):
        self.db.add(Student(name="Navya", qualification="B.Tech", preparation_level="Intermediate", study_hours=3))
        self.db.commit()

        first = auth_service.register_user(self.db, "Navya", "n@x.co", "password1")
        self.assertEqual(self.db.query(Student).one().user_id, first["user"]["id"])

        # a second account must not get anyone else's data
        self.db.add(Student(name="Orphan2", qualification="12th", preparation_level="Beginner", study_hours=1))
        self.db.commit()
        second = auth_service.register_user(self.db, "Other", "o@x.co", "password1")
        mine = self.db.query(Student).filter(Student.user_id == second["user"]["id"]).count()
        self.assertEqual(mine, 0)


class SeedTests(unittest.TestCase):
    def setUp(self):
        self.db, self.engine, self.path = make_session()

    def tearDown(self):
        self.db.close(); self.engine.dispose(); os.remove(self.path)

    def test_seed_loads_expected_data(self):
        summary = seed_ssc(self.db)
        self.assertEqual(self.db.query(SSCExam).count(), 9)
        self.assertEqual(self.db.query(SSCNotification).count(), 2)
        self.assertEqual(summary["exams_added"], 9)
        available = {e.code for e in self.db.query(SSCExam).filter_by(data_status="available")}
        self.assertEqual(available, {"CGL", "CHSL"})

    def test_seed_twice_creates_no_duplicates(self):
        seed_ssc(self.db); seed_ssc(self.db)
        self.assertEqual(self.db.query(SSCExam).count(), 9)
        self.assertEqual(self.db.query(SSCNotification).count(), 2)

    def test_database_blocks_duplicate_notification(self):
        seed_ssc(self.db)
        self.db.add(SSCNotification(exam_code="CGL", notification_ref="CGL-2026", title="dup"))
        with self.assertRaises(IntegrityError):
            self.db.commit()
        self.db.rollback()

    def test_official_record_is_never_overwritten(self):
        seed_ssc(self.db)
        n = self.db.query(SSCNotification).filter_by(notification_ref="CGL-2026").one()
        n.verification = "official"; n.vacancies = 9999
        self.db.commit()

        summary = seed_ssc(self.db)
        self.assertEqual(summary["skipped_official"], 1)
        n = self.db.query(SSCNotification).filter_by(notification_ref="CGL-2026").one()
        self.assertEqual(n.vacancies, 9999)

    def test_every_notification_has_a_source_and_verified_date(self):
        seed_ssc(self.db)
        for n in self.db.query(SSCNotification):
            self.assertTrue(n.source_url and n.sources)
            self.assertIsNotNone(n.last_verified)
            self.assertIn(n.verification, ("official", "secondary"))

    def test_pattern_marks_add_up(self):
        seed_ssc(self.db)
        for code in ("CGL", "CHSL"):
            tier1 = self.db.query(SSCExam).filter_by(code=code).one().pattern[0]
            self.assertEqual(sum(s["questions"] for s in tier1["sections"]), tier1["total_questions"])
            self.assertEqual(sum(s["marks"] for s in tier1["sections"]), tier1["total_marks"])


class SSCServiceTests(unittest.TestCase):
    def setUp(self):
        self.db, self.engine, self.path = make_session()
        seed_ssc(self.db)

    def tearDown(self):
        self.db.close(); self.engine.dispose(); os.remove(self.path)

    def test_status_on_3_nov_2026(self):
        today = date(2026, 11, 3)
        cgl = ssc_service.get_exam(self.db, "cgl", today)          # lower-case works
        chsl = ssc_service.get_exam(self.db, "CHSL", today)
        self.assertEqual(cgl["latest_notification"]["status"], "Tier 1 exam window over. Result awaited")
        self.assertEqual(chsl["latest_notification"]["status"], "Applications closed. Tier 1 starts in 27 days")

    def test_status_while_applications_are_open(self):
        chsl = ssc_service.get_exam(self.db, "CHSL", date(2026, 9, 20))
        self.assertEqual(chsl["latest_notification"]["application_status"], "open")

    def test_exam_in_progress(self):
        chsl = ssc_service.get_exam(self.db, "CHSL", date(2026, 12, 5))
        self.assertEqual(chsl["latest_notification"]["exam_stage"], "ongoing")

    def test_missing_values_are_null_not_invented(self):
        chsl = ssc_service.get_exam(self.db, "CHSL", date(2026, 11, 3))["latest_notification"]
        self.assertIsNone(chsl["tier2_info"])
        self.assertIsNone(chsl["notice_pdf_url"])
        mts = ssc_service.get_exam(self.db, "MTS")
        self.assertEqual(mts["data_status"], "pending")
        self.assertIsNone(mts["latest_notification"])
        self.assertIsNone(mts["qualification"])

    def test_unknown_exam_returns_none(self):
        self.assertIsNone(ssc_service.get_exam(self.db, "XYZ"))

    def test_list_puts_available_exams_first(self):
        codes = [e["code"] for e in ssc_service.list_exams(self.db)["exams"]]
        self.assertEqual(set(codes[:2]), {"CGL", "CHSL"})
        self.assertEqual(len(codes), 9)

    def test_calendar_sorted_and_marks_past(self):
        cal = ssc_service.get_calendar(self.db, date(2026, 11, 3))
        dates = [e["date"] for e in cal["events"]]
        self.assertEqual(dates, sorted(dates))
        by_label = {(e["exam_code"], e["label"]): e for e in cal["events"]}
        self.assertTrue(by_label[("CGL", "Last date to apply")]["is_past"])
        self.assertFalse(by_label[("CHSL", "Tier 1 exam starts")]["is_past"])


class MigrationTests(unittest.TestCase):
    def test_old_students_table_gets_new_columns_and_keeps_data(self):
        handle, path = tempfile.mkstemp(suffix=".db"); os.close(handle)
        engine = create_engine(f"sqlite:///{path}")

        # The students table exactly as it was in the uploaded aspirixa.db
        with engine.connect() as c:
            c.execute(text("""CREATE TABLE students (
                id INTEGER NOT NULL, name VARCHAR NOT NULL, qualification VARCHAR NOT NULL,
                target_exam VARCHAR, preparation_level VARCHAR NOT NULL, study_hours FLOAT NOT NULL,
                subject_preferences VARCHAR, age INTEGER, interested_field VARCHAR,
                learning_preferences VARCHAR, PRIMARY KEY (id))"""))
            c.execute(text("INSERT INTO students (name, qualification, preparation_level, study_hours) "
                           "VALUES ('Navya','B.Tech','Intermediate',3)"))
            c.commit()

        original_engine = init_db.engine
        init_db.engine = engine
        try:
            init_db.init_database()
            init_db.init_database()          # running twice must be harmless
        finally:
            init_db.engine = original_engine

        with engine.connect() as c:
            columns = {r[1] for r in c.execute(text("PRAGMA table_info(students)"))}
            self.assertIn("user_id", columns)
            self.assertEqual(c.execute(text("SELECT name, user_id FROM students")).one(), ("Navya", None))
            tables = {r[0] for r in c.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))}
            self.assertTrue({"users", "ssc_exams", "ssc_notifications"} <= tables)

        engine.dispose(); os.remove(path)


if __name__ == "__main__":
    unittest.main()
