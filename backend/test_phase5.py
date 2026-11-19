"""
Phase 5 tests: saved results and the adaptive topic chooser.

Run from the backend folder:   python -m unittest test_phase5
(The database tests need SQLAlchemy and are skipped if it is missing.)
"""
import unittest

from services.adaptive_quiz import choose_topic, get_next_question
from services.bkt import classify_topic
from services.question_bank import load_questions

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.connection import Base
    from database import models
    from services.progress import (
        clamp_mastery, save_topic_mastery, get_mastery_map, get_weak_topics
    )
    HAVE_SQLALCHEMY = True
except ImportError:
    HAVE_SQLALCHEMY = False



import test_support

_undo_bank = None


def setUpModule():
    global _undo_bank
    _undo_bank = test_support.use_seeded_test_bank()


def tearDownModule():
    if _undo_bank:
        _undo_bank()

class ChooseTopicTests(unittest.TestCase):
    def test_new_student_gets_a_topic(self):
        topic, mastery = choose_topic({})
        self.assertIsNotNone(topic)
        self.assertEqual(mastery, 0.5)

    def test_weakest_topic_is_chosen(self):
        topic, mastery = choose_topic({
            "Percentages": 0.8, "Number Series": 0.2,
            "Grammar": 0.6, "Indian Polity": 0.7,
        })
        self.assertEqual(topic, "Number Series")
        self.assertEqual(mastery, 0.2)

    def test_answered_questions_are_skipped(self):
        # Once every Number Series question is used, move on to another topic
        used = [int(q["question_id"]) for q in load_questions() if q["topic"] == "Number Series"]
        topic, _ = choose_topic(
            {"Number Series": 0.1, "Percentages": 0.9, "Grammar": 0.9, "Indian Polity": 0.9},
            answered_question_ids=used,
        )
        self.assertNotEqual(topic, "Number Series")

    def test_no_questions_left(self):
        topic, mastery = choose_topic({}, answered_question_ids=[int(q["question_id"]) for q in load_questions()])
        self.assertIsNone(topic)
        self.assertIsNone(mastery)

    def test_low_mastery_gets_easy_question(self):
        question = get_next_question("Percentages", 0.2, [])
        self.assertEqual(question["difficulty"], "Easy")

    def test_high_mastery_gets_hard_question(self):
        question = get_next_question("Percentages", 0.9, [])
        self.assertEqual(question["difficulty"], "Hard")


@unittest.skipUnless(HAVE_SQLALCHEMY, "SQLAlchemy is not installed")
class SavedMasteryTests(unittest.TestCase):
    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

    def tearDown(self):
        self.db.close()

    def test_save_creates_then_updates_one_row(self):
        save_topic_mastery(self.db, 1, "Percentages", 0.30, "diagnostic", "Quantitative Aptitude")
        self.db.commit()
        save_topic_mastery(self.db, 1, "Percentages", 0.75, "quiz")
        self.db.commit()

        rows = self.db.query(models.TopicMastery).all()
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].mastery, 0.75)
        self.assertEqual(rows[0].status, classify_topic(0.75))
        self.assertEqual(rows[0].source, "quiz")
        self.assertEqual(rows[0].subject, "Quantitative Aptitude")

    def test_each_student_has_own_mastery(self):
        save_topic_mastery(self.db, 1, "Grammar", 0.2, "diagnostic")
        save_topic_mastery(self.db, 2, "Grammar", 0.9, "diagnostic")
        self.db.commit()
        self.assertEqual(get_mastery_map(self.db, 1), {"Grammar": 0.2})
        self.assertEqual(get_mastery_map(self.db, 2), {"Grammar": 0.9})

    def test_weak_topics_are_listed_weakest_first(self):
        save_topic_mastery(self.db, 1, "Grammar", 0.35, "diagnostic")
        save_topic_mastery(self.db, 1, "Percentages", 0.10, "diagnostic")
        save_topic_mastery(self.db, 1, "Indian Polity", 0.90, "diagnostic")
        self.db.commit()
        self.assertEqual(get_weak_topics(self.db, 1), ["Percentages", "Grammar"])

    def test_clamp_mastery(self):
        self.assertEqual(clamp_mastery(None), 0.5)
        self.assertEqual(clamp_mastery(1.7), 1.0)
        self.assertEqual(clamp_mastery(-3), 0.0)


if __name__ == "__main__":
    unittest.main()
