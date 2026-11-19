"""
Phase 8 tests (Step 1): question bank in the database.

Run from the backend folder:   python -m unittest test_phase8 -v

Part A (validation rules) needs only the Python standard library.
Part B (database) needs SQLAlchemy and is skipped if it is missing.
"""
import csv
import os
import unittest
from pathlib import Path

from services.question_validation import (
    validate_row, validate_rows, parse_tiers, duplicate_key, SUBJECTS,
)

CSV_PATH = Path(__file__).resolve().parents[1] / "Dataset" / "questions.csv"

try:
    from sqlalchemy import inspect
    HAVE_SQLALCHEMY = True
except ImportError:
    HAVE_SQLALCHEMY = False


def good_row(**changes):
    row = {
        "question_id": "1", "subject": "Quantitative Aptitude", "topic": "Percentages",
        "difficulty": "Easy", "question": "What is 20% of 200?",
        "option_a": "20", "option_b": "30", "option_c": "40", "option_d": "50",
        "correct_answer": "C", "diagnostic": "yes",
    }
    row.update(changes)
    return row


# ======================================================================
# PART A - validation rules (no database)
# ======================================================================
class ValidationRuleTests(unittest.TestCase):
    def test_a_good_row_is_accepted(self):
        clean, errors = validate_row(good_row())
        self.assertEqual(errors, [])
        self.assertEqual(clean["id"], 1)
        self.assertTrue(clean["is_diagnostic"])
        self.assertEqual(clean["tiers"], [])

    def test_old_subject_labels_are_renamed(self):
        clean, _ = validate_row(good_row(subject="Reasoning"))
        self.assertEqual(clean["subject"], "General Intelligence & Reasoning")
        clean, _ = validate_row(good_row(subject="English"))
        self.assertEqual(clean["subject"], "English Language")

    def test_unknown_subject_is_refused(self):
        clean, errors = validate_row(good_row(subject="Computer Knowledge"))
        self.assertIsNone(clean)
        self.assertTrue(any("subject" in e for e in errors))

    def test_answer_must_be_a_to_d(self):
        for bad in ["E", "", "Kerala", "AB"]:
            clean, errors = validate_row(good_row(correct_answer=bad))
            self.assertIsNone(clean, bad)
            self.assertTrue(any("correct_answer" in e for e in errors))

    def test_lowercase_answer_and_difficulty_are_tidied(self):
        clean, errors = validate_row(good_row(correct_answer="c", difficulty="hard"))
        self.assertEqual(errors, [])
        self.assertEqual(clean["correct_answer"], "C")
        self.assertEqual(clean["difficulty"], "Hard")

    def test_difficulty_must_be_easy_medium_hard(self):
        for bad in ["Moderate", "", "Very Hard"]:
            clean, _ = validate_row(good_row(difficulty=bad))
            self.assertIsNone(clean, bad)

    def test_four_options_are_required(self):
        clean, errors = validate_row(good_row(option_d=""))
        self.assertIsNone(clean)
        self.assertTrue(any("four options" in e for e in errors))

    def test_options_must_differ(self):
        clean, errors = validate_row(good_row(option_a="40", option_c="40"))
        self.assertIsNone(clean)
        self.assertTrue(any("different" in e for e in errors))

    def test_empty_question_or_topic_is_refused(self):
        self.assertIsNone(validate_row(good_row(question=""))[0])
        self.assertIsNone(validate_row(good_row(topic=""))[0])

    def test_bad_id_is_refused(self):
        for bad in ["", "abc", "0", "-3"]:
            self.assertIsNone(validate_row(good_row(question_id=bad))[0], bad)

    def test_tiers_are_parsed_and_checked(self):
        self.assertEqual(parse_tiers("CGL; chsl"), ["CGL", "CHSL"])
        self.assertEqual(parse_tiers(""), [])
        clean, errors = validate_row(good_row(exam_tiers="CGL;UPSC"))
        self.assertIsNone(clean)
        self.assertTrue(any("tier" in e for e in errors))
        clean, _ = validate_row(good_row(exam_tiers="CGL;JE"))
        self.assertEqual(clean["tiers"], ["CGL", "JE"])


class DuplicateAndReimportRuleTests(unittest.TestCase):
    def test_duplicate_inside_the_file_is_refused(self):
        rows = [good_row(question_id="1"), good_row(question_id="2")]   # same text + options
        good, rejected, unchanged = validate_rows(rows)
        self.assertEqual([g["id"] for g in good], [1])
        self.assertEqual(len(rejected), 1)
        self.assertEqual(rejected[0]["line"], 3)
        self.assertTrue(any("duplicate" in e for e in rejected[0]["errors"]))

    def test_duplicate_is_found_even_with_different_spacing_and_case(self):
        rows = [good_row(question_id="1"),
                good_row(question_id="2", question="  what is 20% of 200 ?  ",
                         option_a="50", option_b="40", option_c="30", option_d="20")]
        good, rejected, _ = validate_rows(rows)
        self.assertEqual(len(good), 1)
        self.assertEqual(len(rejected), 1)

    def test_same_text_with_different_options_is_not_a_duplicate(self):
        rows = [good_row(question_id="1"),
                good_row(question_id="2", option_a="1", option_b="2", option_c="3", option_d="4")]
        good, rejected, _ = validate_rows(rows)
        self.assertEqual(len(good), 2)
        self.assertEqual(rejected, [])

    def test_same_id_twice_in_the_file(self):
        rows = [good_row(question_id="1"), good_row(question_id="1", question="Another one?")]
        good, rejected, _ = validate_rows(rows)
        self.assertEqual(len(good), 1)
        self.assertTrue(any("twice" in e for e in rejected[0]["errors"]))

    def test_same_content_already_in_database_is_unchanged(self):
        row = good_row()
        clean, _ = validate_row(row)
        key = duplicate_key(clean["question"],
                            [clean["option_a"], clean["option_b"], clean["option_c"], clean["option_d"]])
        good, rejected, unchanged = validate_rows([row], existing_keys={key: 1}, existing_ids={1})
        self.assertEqual((good, rejected, unchanged), ([], [], [1]))

    def test_existing_id_with_different_content_is_refused_not_overwritten(self):
        good, rejected, unchanged = validate_rows(
            [good_row(question="A completely different question?")],
            existing_keys={}, existing_ids={1},
        )
        self.assertEqual(good, [])
        self.assertEqual(unchanged, [])
        self.assertTrue(any("different content" in e for e in rejected[0]["errors"]))

    def test_new_row_duplicating_a_database_question_is_refused(self):
        clean, _ = validate_row(good_row())
        key = duplicate_key(clean["question"],
                            [clean["option_a"], clean["option_b"], clean["option_c"], clean["option_d"]])
        good, rejected, _ = validate_rows([good_row(question_id="9")], existing_keys={key: 1}, existing_ids={1})
        self.assertEqual(good, [])
        self.assertTrue(any("duplicate of question 1" in e for e in rejected[0]["errors"]))

    def test_a_bad_row_does_not_stop_the_good_rows(self):
        rows = [good_row(question_id="1"),
                good_row(question_id="2", correct_answer="Z", question="Second?"),
                good_row(question_id="3", question="Third?")]
        good, rejected, _ = validate_rows(rows)
        self.assertEqual([g["id"] for g in good], [1, 3])
        self.assertEqual(rejected[0]["question_id"], "2")


class SeedCsvTests(unittest.TestCase):
    """The real Dataset/questions.csv must pass every rule."""

    def setUp(self):
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            self.rows = list(csv.DictReader(f))

    def test_all_seed_rows_are_valid(self):
        good, rejected, _ = validate_rows(self.rows)
        self.assertEqual(rejected, [])
        self.assertEqual(len(good), len(self.rows))

    def test_seed_subjects_end_up_in_the_four_official_names(self):
        good, _, _ = validate_rows(self.rows)
        self.assertTrue({g["subject"] for g in good} <= set(SUBJECTS))

    def test_seed_has_24_diagnostic_questions(self):
        good, _, _ = validate_rows(self.rows)
        self.assertEqual(sum(g["is_diagnostic"] for g in good), 24)


# ======================================================================
# PART B - database (needs SQLAlchemy)
# ======================================================================
@unittest.skipUnless(HAVE_SQLALCHEMY, "SQLAlchemy is not installed")
class DatabaseTestCase(unittest.TestCase):
    def setUp(self):
        import test_support
        from services import question_bank
        self.question_bank = question_bank
        self.factory = test_support.make_session_factory()
        self.db = self.factory()
        question_bank.set_session_factory(self.factory)
        self._old_env = os.environ.pop("SERVE_DRAFT_QUESTIONS", None)

    def tearDown(self):
        self.question_bank.set_session_factory(None)
        self.db.close()
        os.environ.pop("SERVE_DRAFT_QUESTIONS", None)
        if self._old_env is not None:
            os.environ["SERVE_DRAFT_QUESTIONS"] = self._old_env

    def seed(self):
        from services.question_import import import_csv
        return import_csv(self.db, CSV_PATH)

    def review_all(self):
        from database.models import Question
        self.db.query(Question).update({"status": "reviewed"})
        self.db.commit()


class ImportTests(DatabaseTestCase):
    def test_seed_import_creates_72_draft_questions_without_tiers(self):
        from database.models import Question, QuestionTier
        result = self.seed()
        self.assertEqual(result["imported"], 72)
        self.assertEqual(result["rejected"], [])
        self.assertEqual(self.db.query(Question).count(), 72)
        self.assertEqual(self.db.query(Question).filter(Question.status != "draft").count(), 0)
        self.assertEqual(self.db.query(QuestionTier).count(), 0)
        self.assertEqual(self.db.query(Question).filter(Question.is_diagnostic.is_(True)).count(), 24)

    def test_default_source_is_not_the_hand_built_claim(self):
        from database.models import Question
        self.seed()
        sources = {q.source for q in self.db.query(Question).all()}
        self.assertEqual(sources, {"seed-csv-unverified"})

    def test_source_can_be_set_once_authorship_is_confirmed(self):
        from database.models import Question
        from services.question_import import import_csv
        import_csv(self.db, CSV_PATH, source="original-hand-built")
        self.assertEqual({q.source for q in self.db.query(Question).all()}, {"original-hand-built"})

    def test_subjects_use_the_four_official_names(self):
        from database.models import Question
        self.seed()
        subjects = {q.subject for q in self.db.query(Question).all()}
        self.assertEqual(subjects, set(SUBJECTS))

    def test_reimport_is_safe(self):
        from database.models import Question
        self.seed()
        again = self.seed()
        self.assertEqual(again["imported"], 0)
        self.assertEqual(len(again["unchanged"]), 72)
        self.assertEqual(again["rejected"], [])
        self.assertEqual(self.db.query(Question).count(), 72)

    def test_reimport_does_not_undo_a_review(self):
        from database.models import Question
        self.seed()
        self.db.query(Question).filter(Question.id == 1).update({"status": "reviewed"})
        self.db.commit()
        self.seed()
        self.assertEqual(self.db.get(Question, 1).status, "reviewed")

    def test_bad_rows_are_refused_and_reported_good_rows_imported(self):
        from database.models import Question
        from services.question_import import import_rows
        rows = [good_row(question_id="1"),
                good_row(question_id="2", correct_answer="Z", question="Second?"),
                good_row(question_id="3", question="Third?")]
        result = import_rows(self.db, rows)
        self.assertEqual(result["imported"], 2)
        self.assertEqual(len(result["rejected"]), 1)
        self.assertIn("line 3", result["report"])
        self.assertEqual(self.db.query(Question).count(), 2)

    def test_strict_mode_imports_nothing_if_any_row_is_bad(self):
        from database.models import Question
        from services.question_import import import_rows
        rows = [good_row(question_id="1"), good_row(question_id="2", difficulty="Odd", question="Second?")]
        result = import_rows(self.db, rows, strict=True)
        self.assertEqual(result["imported"], 0)
        self.assertEqual(self.db.query(Question).count(), 0)

    def test_a_csv_cannot_create_a_reviewed_question(self):
        from database.models import Question
        from services.question_import import import_rows
        import_rows(self.db, [good_row(status="reviewed")])
        self.assertEqual(self.db.query(Question).first().status, "draft")

    def test_tiers_from_a_csv_column_are_stored_many_per_question(self):
        from database.models import Question
        from services.question_import import import_rows
        import_rows(self.db, [good_row(exam_tiers="CGL;CHSL;JE")])
        tiers = sorted(t.tier for t in self.db.query(Question).first().tiers)
        self.assertEqual(tiers, ["CGL", "CHSL", "JE"])

    def test_composite_index_exists(self):
        indexes = inspect(self.db.bind).get_indexes("questions")
        columns = [tuple(i["column_names"]) for i in indexes]
        self.assertIn(("subject", "topic", "difficulty"), columns)


class ServingRuleTests(DatabaseTestCase):
    def test_drafts_are_not_served_by_default(self):
        self.seed()
        qb = self.question_bank
        self.assertEqual(qb.load_questions(), [])
        self.assertEqual(qb.load_diagnostic_questions(), [])
        self.assertIsNone(qb.get_question(1))
        self.assertEqual(qb.available_topics(), [])
        self.assertIsNone(qb.next_question("Percentages", "Easy"))

    def test_drafts_are_served_only_with_the_local_testing_flag(self):
        self.seed()
        os.environ["SERVE_DRAFT_QUESTIONS"] = "1"
        self.assertEqual(len(self.question_bank.load_questions()), 72)

    def test_flag_value_must_be_exactly_1(self):
        self.seed()
        for value in ["0", "true", "yes", ""]:
            os.environ["SERVE_DRAFT_QUESTIONS"] = value
            self.assertEqual(self.question_bank.load_questions(), [], value)

    def test_reviewed_questions_are_served(self):
        self.seed()
        self.review_all()
        qb = self.question_bank
        self.assertEqual(len(qb.load_questions()), 72)
        self.assertEqual(len(qb.load_diagnostic_questions()), 24)
        self.assertEqual(qb.get_question(1)["correct_answer"], "C")

    def test_only_the_reviewed_ones_are_served_when_mixed(self):
        from database.models import Question
        self.seed()
        self.db.query(Question).filter(Question.id.in_([1, 2, 3])).update(
            {"status": "reviewed"}, synchronize_session=False)
        self.db.commit()
        ids = [q["question_id"] for q in self.question_bank.load_questions()]
        self.assertEqual(ids, [1, 2, 3])

    def test_tiers_are_not_used_for_filtering_yet(self):
        from database.models import Question
        self.seed()
        self.review_all()
        # only question 1 gets a tier; all 72 must still be served
        self.db.get(Question, 1).tiers = []
        self.assertEqual(len(self.question_bank.load_questions()), 72)


class SameBehaviourAsCsvTests(DatabaseTestCase):
    """The new SQL selection must pick exactly what the old CSV code picked."""

    def setUp(self):
        super().setUp()
        self.seed()
        self.review_all()
        with open(CSV_PATH, encoding="utf-8-sig", newline="") as f:
            self.csv_rows = list(csv.DictReader(f))
        for row in self.csv_rows:          # old files had the old subject labels
            row["subject"] = {"Reasoning": "General Intelligence & Reasoning",
                              "English": "English Language"}.get(row["subject"], row["subject"])

    # ---- the OLD algorithms, copied from the CSV version ----
    def old_choose_topic(self, mastery_by_topic, answered, default=0.5):
        answered = set(answered or [])
        available = {}
        for q in self.csv_rows:
            if int(q["question_id"]) in answered:
                continue
            available.setdefault(q["topic"], mastery_by_topic.get(q["topic"], default))
        if not available:
            return None, None
        topic = min(available, key=available.get)
        return topic, available[topic]

    def old_next_question_id(self, topic, difficulty, answered):
        match = [q for q in self.csv_rows if q["topic"] == topic and q["difficulty"] == difficulty
                 and int(q["question_id"]) not in answered]
        if not match:
            match = [q for q in self.csv_rows if q["topic"] == topic and int(q["question_id"]) not in answered]
        return int(match[0]["question_id"]) if match else None

    def test_loaded_rows_equal_csv_rows(self):
        new = self.question_bank.load_questions()
        self.assertEqual(len(new), len(self.csv_rows))
        for n, o in zip(new, self.csv_rows):
            self.assertEqual(n["question_id"], int(o["question_id"]))
            for key in ["subject", "topic", "difficulty", "question",
                        "option_a", "option_b", "option_c", "option_d", "correct_answer"]:
                self.assertEqual(n[key], o[key], f"question {o['question_id']} {key}")

    def test_diagnostic_set_equals_csv_diagnostic_rows(self):
        old = [int(q["question_id"]) for q in self.csv_rows if q["diagnostic"].strip().lower() == "yes"]
        new = [q["question_id"] for q in self.question_bank.load_diagnostic_questions()]
        self.assertEqual(new, old)

    def test_next_question_matches_old_logic_for_every_topic_difficulty_and_history(self):
        from services.adaptive_quiz import get_next_question, get_target_difficulty
        topics = sorted({q["topic"] for q in self.csv_rows})
        all_ids = [int(q["question_id"]) for q in self.csv_rows]
        histories = [[], all_ids[:10], all_ids[::2], all_ids[5:40], all_ids]
        for topic in topics:
            for mastery in [0.1, 0.39, 0.4, 0.55, 0.69, 0.7, 0.95]:
                for answered in histories:
                    expected = self.old_next_question_id(topic, get_target_difficulty(mastery), set(answered))
                    got = get_next_question(topic, mastery, list(answered))
                    self.assertEqual(got["question_id"] if got else None, expected,
                                     f"{topic} mastery={mastery} answered={len(answered)}")

    def test_choose_topic_matches_old_logic(self):
        from services.adaptive_quiz import choose_topic
        all_ids = [int(q["question_id"]) for q in self.csv_rows]
        topics = sorted({q["topic"] for q in self.csv_rows})
        masteries = [
            {}, {"Number Series": 0.2}, {t: 0.5 for t in topics},
            {t: 0.9 for t in topics}, {t: 0.3 for t in topics},
            {"Percentages": 0.1, "Grammar": 0.1},
        ]
        histories = [[], all_ids[:20], all_ids[::3], all_ids[:-1], all_ids]
        for m in masteries:
            for answered in histories:
                self.assertEqual(choose_topic(m, answered), self.old_choose_topic(m, answered), (m, len(answered)))

    def test_answered_questions_are_never_returned(self):
        from services.adaptive_quiz import get_next_question
        answered = []
        while True:
            q = get_next_question("Percentages", 0.5, answered)
            if q is None:
                break
            self.assertNotIn(q["question_id"], answered)
            answered.append(q["question_id"])
        # every Percentages question was served exactly once (count taken from the CSV itself)
        expected = sorted(int(r["question_id"]) for r in self.csv_rows if r["topic"] == "Percentages")
        self.assertEqual(sorted(answered), expected)
        self.assertEqual(len(expected), 6)       # seed file: ids 1, 2, 3, 13, 14, 15


class QuestionTierTableTests(DatabaseTestCase):
    def test_a_question_can_have_several_tiers(self):
        from database.models import Question, QuestionTier
        self.seed()
        q = self.db.get(Question, 1)
        q.tiers = [QuestionTier(tier="CGL"), QuestionTier(tier="MTS")]
        self.db.commit()
        self.db.expire_all()
        self.assertEqual(sorted(t.tier for t in self.db.get(Question, 1).tiers), ["CGL", "MTS"])

    def test_the_same_tier_cannot_be_stored_twice_for_one_question(self):
        from sqlalchemy import insert
        from sqlalchemy.exc import IntegrityError
        from database.models import QuestionTier
        self.seed()
        self.db.execute(insert(QuestionTier).values(question_id=1, tier="CGL"))
        with self.assertRaises(IntegrityError):
            self.db.execute(insert(QuestionTier).values(question_id=1, tier="CGL"))
        self.db.rollback()


class ReviewToolTests(DatabaseTestCase):
    def setUp(self):
        super().setUp()
        self.seed()
        from services import question_review
        self.qr = question_review

    def test_nothing_is_reviewed_after_import(self):
        self.assertEqual(self.qr.summary(self.db)["reviewed"], 0)
        self.assertEqual(self.qr.summary(self.db)["draft"], 72)

    def test_review_needs_an_explanation(self):
        with self.assertRaises(self.qr.ReviewError):
            self.qr.mark_reviewed(self.db, 1, "Tester", "C")       # seed rows have no explanation
        self.assertEqual(self.qr.list_questions(self.db, status="reviewed"), [])

    def test_review_succeeds_with_explanation_and_matching_answer(self):
        self.qr.edit_question(self.db, 1, explanation="20% of 200 = 0.2 x 200 = 40.")
        q = self.qr.mark_reviewed(self.db, 1, "Tester", "c")
        self.assertEqual(q.status, "reviewed")
        self.assertEqual(q.reviewed_by, "Tester")
        self.assertIsNotNone(q.reviewed_at)

    def test_wrong_answer_does_not_pass_review(self):
        self.qr.edit_question(self.db, 1, explanation="x")
        with self.assertRaises(self.qr.ReviewError):
            self.qr.mark_reviewed(self.db, 1, "Tester", "A")
        self.assertEqual(self.qr.list_questions(self.db, status="reviewed"), [])

    def test_blank_reviewer_or_invalid_letter_is_refused(self):
        self.qr.edit_question(self.db, 1, explanation="x")
        for reviewer, letter in [("", "C"), ("  ", "C"), ("Tester", ""), ("Tester", "Z")]:
            with self.assertRaises(self.qr.ReviewError):
                self.qr.mark_reviewed(self.db, 1, reviewer, letter)

    def test_missing_explanation_can_be_allowed_explicitly(self):
        q = self.qr.mark_reviewed(self.db, 1, "Tester", "C", allow_missing_explanation=True)
        self.assertEqual(q.status, "reviewed")

    def test_editing_a_reviewed_question_sends_it_back_to_draft(self):
        self.qr.edit_question(self.db, 1, explanation="x")
        self.qr.mark_reviewed(self.db, 1, "Tester", "C")
        q = self.qr.edit_question(self.db, 1, difficulty="medium")
        self.assertEqual(q.status, "draft")
        self.assertIsNone(q.reviewed_by)
        self.assertEqual(q.difficulty, "Medium")
        self.assertEqual(q.version, 3)      # 1 import, +1 explanation edit, +1 difficulty edit

    def test_edit_validates_values(self):
        with self.assertRaises(self.qr.ReviewError):
            self.qr.edit_question(self.db, 1, difficulty="Odd")
        with self.assertRaises(self.qr.ReviewError):
            self.qr.edit_question(self.db, 1, correct_answer="E")
        with self.assertRaises(self.qr.ReviewError):
            self.qr.edit_question(self.db, 1, subject="Computer Knowledge")
        with self.assertRaises(self.qr.ReviewError):
            self.qr.edit_question(self.db, 1, tiers=["CGL", "UPSC"])

    def test_tiers_can_be_assigned_and_cleared(self):
        q = self.qr.edit_question(self.db, 1, tiers=["CGL", "CHSL"])
        self.assertEqual(sorted(t.tier for t in q.tiers), ["CGL", "CHSL"])
        q = self.qr.edit_question(self.db, 1, tiers=[])
        self.assertEqual(q.tiers, [])

    def test_unknown_question_id(self):
        with self.assertRaises(self.qr.ReviewError):
            self.qr.mark_reviewed(self.db, 9999, "Tester", "A")

    def test_summary_counts_reviewed_diagnostic_questions(self):
        self.qr.edit_question(self.db, 1, explanation="x")      # question 1 is a diagnostic question
        self.qr.mark_reviewed(self.db, 1, "Tester", "C")
        s = self.qr.summary(self.db)
        self.assertEqual((s["reviewed"], s["draft"]), (1, 71))
        self.assertEqual((s["diagnostic_reviewed"], s["diagnostic_total"]), (1, 24))

    def test_list_filters(self):
        rows = self.qr.list_questions(self.db, status="draft", subject="Reasoning", topic="Number Series")
        self.assertTrue(rows)
        self.assertTrue(all(q.subject == "General Intelligence & Reasoning" for q in rows))


class SyllabusSubjectMatchTests(DatabaseTestCase):
    """The renamed subjects must still bring the right syllabus subject to the front."""

    def _topics(self):
        from database.models import SyllabusTopic
        subjects = ["Quantitative Aptitude", "General Intelligence and Reasoning",
                    "English Comprehension", "General Awareness"]
        for i, subject in enumerate(subjects, start=1):
            self.db.add(SyllabusTopic(key=f"k{i}", exam_code="CGL", tier="Tier 1", subject=subject,
                                      area="a", topic=f"t{i}", subtopics=[], sort_order=i))
        self.db.commit()

    def test_new_subject_names_still_match_the_syllabus(self):
        from services.study_log import pending_syllabus_topics
        self._topics()
        first = pending_syllabus_topics(self.db, 1, "CGL", ["General Intelligence & Reasoning"])[0]
        self.assertEqual(first["subject"], "General Intelligence and Reasoning")
        first = pending_syllabus_topics(self.db, 1, "CGL", ["English Language"])[0]
        self.assertEqual(first["subject"], "English Comprehension")

    def test_old_subject_names_still_work(self):
        from services.study_log import pending_syllabus_topics
        self._topics()
        self.assertEqual(
            pending_syllabus_topics(self.db, 1, "CGL", ["Reasoning"])[0]["subject"],
            "General Intelligence and Reasoning")
        self.assertEqual(
            pending_syllabus_topics(self.db, 1, "CGL", ["English"])[0]["subject"],
            "English Comprehension")


class AnalyticsLabelTests(unittest.TestCase):
    def test_new_and_old_subject_labels_have_short_names(self):
        from services.analytics import SHORT_SUBJECT
        self.assertEqual(SHORT_SUBJECT["General Intelligence & Reasoning"], "Reasoning")
        self.assertEqual(SHORT_SUBJECT["English Language"], "English")
        self.assertEqual(SHORT_SUBJECT["Reasoning"], "Reasoning")
        self.assertEqual(SHORT_SUBJECT["English"], "English")


if __name__ == "__main__":
    unittest.main()