"""
Phase 6 tests: the question bank and the Performance numbers.

Run from the backend folder:   python -m unittest test_phase6
"""
import unittest
from collections import Counter, defaultdict
from datetime import date

from services.question_bank import load_questions, load_diagnostic_questions
from services.analytics import compute_analytics



import test_support

_undo_bank = None


def setUpModule():
    global _undo_bank
    _undo_bank = test_support.use_seeded_test_bank()


def tearDownModule():
    if _undo_bank:
        _undo_bank()

class QuestionBankTests(unittest.TestCase):
    def setUp(self):
        self.questions = load_questions()

    def test_ids_are_unique(self):
        ids = [q["question_id"] for q in self.questions]
        self.assertEqual(len(ids), len(set(ids)))

    def test_every_question_is_complete(self):
        for q in self.questions:
            options = [q["option_a"], q["option_b"], q["option_c"], q["option_d"]]
            self.assertTrue(all(o.strip() for o in options), q["question_id"])
            self.assertEqual(len(set(options)), 4, f"duplicate options in question {q['question_id']}")
            self.assertIn(q["correct_answer"], ["A", "B", "C", "D"], q["question_id"])
            self.assertIn(q["difficulty"], ["Easy", "Medium", "Hard"], q["question_id"])

    def test_each_topic_has_every_difficulty_at_least_twice(self):
        levels = defaultdict(Counter)
        for q in self.questions:
            levels[q["topic"]][q["difficulty"]] += 1
        for topic, counts in levels.items():
            for level in ["Easy", "Medium", "Hard"]:
                self.assertGreaterEqual(counts[level], 2, f"{topic} {level}")

    def test_diagnostic_has_easy_medium_hard_for_each_of_its_topics(self):
        levels = defaultdict(Counter)
        for q in load_diagnostic_questions():
            levels[q["topic"]][q["difficulty"]] += 1
        self.assertGreaterEqual(len(levels), 8)
        for topic, counts in levels.items():
            self.assertEqual(dict(counts), {"Easy": 1, "Medium": 1, "Hard": 1}, topic)

    def test_diagnostic_is_a_subset_of_the_bank(self):
        all_ids = {q["question_id"] for q in self.questions}
        self.assertTrue({q["question_id"] for q in load_diagnostic_questions()} <= all_ids)


class AnalyticsTests(unittest.TestCase):
    TODAY = date(2026, 11, 9)

    def test_no_data(self):
        result = compute_analytics([], [], [], today=self.TODAY)
        self.assertFalse(result["has_data"])
        self.assertEqual(result["weekly"]["values"], [])
        self.assertEqual(result["topics"], [])

    def test_numbers_come_from_the_data(self):
        topics = [
            {"topic": "Percentages", "subject": "Quantitative Aptitude", "mastery": 0.30, "status": "Weak"},
            {"topic": "Grammar", "subject": "English", "mastery": 0.90, "status": "Mastered"},
        ]
        attempts = [
            {"date": date(2026, 11, 8), "difficulty": "Easy", "correct": True},
            {"date": date(2026, 11, 8), "difficulty": "Easy", "correct": False},
            {"date": date(2026, 11, 9), "difficulty": "Hard", "correct": True},
            {"date": date(2026, 11, 9), "difficulty": "Hard", "correct": True},
        ]
        diagnostics = [{"total_answered": 12, "correct_answers": 6, "score_percentage": 50.0}]

        result = compute_analytics(topics, attempts, diagnostics, today=self.TODAY)
        cards = {c["id"]: c for c in result["summary"]}

        self.assertTrue(result["has_data"])
        self.assertEqual(cards["acc"]["value"], "75")        # 3 of 4 correct
        self.assertEqual(cards["mastery"]["value"], "60")    # (30 + 90) / 2
        self.assertEqual(cards["solved"]["value"], "16")     # 4 quiz + 12 diagnostic
        self.assertEqual(result["weekly"]["values"], [50, 100])
        self.assertEqual([t["name"] for t in result["topics"]], ["Percentages", "Grammar"])
        self.assertEqual(
            {d["label"]: d["value"] for d in result["difficulty"]},
            {"Easy": 2, "Medium": 0, "Hard": 2},
        )
        self.assertTrue(any("Percentages" in text for text in result["insights"]))

    def test_accuracy_falls_back_to_diagnostic(self):
        diagnostics = [{"total_answered": 12, "correct_answers": 9, "score_percentage": 75.0}]
        result = compute_analytics([], [], diagnostics, today=self.TODAY)
        self.assertEqual(result["summary"][0]["value"], "75")


if __name__ == "__main__":
    unittest.main()
