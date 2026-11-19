"""
Phase 7 tests: eligibility, recommendation scoring, study planner,
diagnostic analysis, feedback and dashboard numbers.

Run from the backend folder:   python -m unittest test_phase7
(Tests that need XGBoost / SHAP / SQLAlchemy are skipped if those are missing.)
"""
import unittest
from datetime import date, timedelta

from services.eligibility import normalize_qualification, get_eligible_exams, evaluate_exams
from services.recommender import (
    subject_alignment, split_subjects, study_match_score, qualification_fit, exam_factors,
)
from ml.topsis import topsis_rank
from services.bkt import update_mastery
from services.study_planner import create_study_plan, allocate_minutes, MIN_SESSION, MAX_SESSION
from services.diagnostic_analysis import analyse_answers, QuestionNotFound
from services.question_bank import load_questions, load_diagnostic_questions
from services.feedback import build_feedback
from services.dashboard import activity_streaks, compute_dashboard_stats
from services.study_log import exam_code_for

try:
    import xgboost, shap  # noqa: F401
    HAVE_ML = True
except ImportError:
    HAVE_ML = False

try:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from database.connection import Base
    from database import models
    HAVE_DB = True
except ImportError:
    HAVE_DB = False



import test_support

_undo_bank = None


def setUpModule():
    global _undo_bank
    _undo_bank = test_support.use_seeded_test_bank()


def tearDownModule():
    if _undo_bank:
        _undo_bank()

class EligibilityTests(unittest.TestCase):
    def test_every_profile_option_is_recognised(self):
        expected = {
            "12th Pass": "12th", "Diploma": "diploma", "B.Tech CSE": "graduation",
            "B.Tech / B.E. (Other)": "graduation", "B.Sc": "graduation", "B.Com": "graduation",
            "B.A.": "graduation", "Postgraduate": "postgraduation", "10th": "10th", "M.Tech": "postgraduation",
        }
        for text, level in expected.items():
            self.assertEqual(normalize_qualification(text), level, text)

    def test_twelfth_pass_cannot_write_graduate_exams(self):
        names = {e["exam_name"] for e in get_eligible_exams("12th Pass")}
        self.assertIn("SSC CHSL", names)
        self.assertNotIn("SSC CGL", names)

    def test_graduate_is_eligible_for_ssc_cgl(self):
        self.assertIn("SSC CGL", {e["exam_name"] for e in get_eligible_exams("B.Sc")})

    def test_age_limit_filters_and_explains(self):
        result = {e["exam_name"]: e for e in evaluate_exams("B.Tech CSE", age=40)}
        self.assertFalse(result["SSC CGL"]["eligible"])
        self.assertTrue(any("Maximum age" in r for r in result["SSC CGL"]["reasons"]))

    def test_dataset_contains_ssc_exams(self):
        names = {e["exam_name"] for e in evaluate_exams("Postgraduate")}
        for ssc in ("SSC CGL", "SSC CHSL", "SSC MTS", "SSC CPO", "SSC GD Constable", "SSC JE"):
            self.assertIn(ssc, names)


class ScoringTests(unittest.TestCase):
    def test_subject_alignment(self):
        pref = ["Quantitative Aptitude", "Reasoning", "English"]
        cgl = split_subjects("Quantitative Aptitude;Reasoning;English;General Awareness")
        self.assertGreater(subject_alignment(pref, cgl), 0.8)
        self.assertEqual(subject_alignment(["English"], split_subjects("Mathematics;Reasoning")), 0.0)
        self.assertEqual(subject_alignment([], cgl), 0.5)

    def test_qualification_fit_prefers_matching_level(self):
        self.assertEqual(qualification_fit("B.Tech CSE", "Graduation"), 1.0)
        self.assertLess(qualification_fit("B.Tech CSE", "10th"), qualification_fit("B.Tech CSE", "12th"))
        self.assertEqual(qualification_fit("12th Pass", "Graduation"), 0.0)

    def test_factor_bars_are_percentages(self):
        exam = {"difficulty": "High", "recommended_hours": "6", "minimum_qualification": "Graduation"}
        f = exam_factors(exam, "B.Tech CSE", "Beginner", 3, 0.8)
        self.assertEqual(f["time"], 50)
        self.assertEqual(f["subject"], 80)
        self.assertLess(f["level"], 100)

    def test_topsis_single_exam_and_ranking(self):
        one = topsis_rank([{"exam_name": "A", "suitability_score": 0.8, "study_match": 0.5,
                            "qualification_fit": 1.0, "difficulty_score": 2}])
        self.assertEqual(one[0]["topsis_score"], 1.0)
        many = topsis_rank([
            {"exam_name": "good", "suitability_score": 0.9, "study_match": 0.9, "qualification_fit": 1.0, "difficulty_score": 1},
            {"exam_name": "poor", "suitability_score": 0.3, "study_match": 0.3, "qualification_fit": 0.25, "difficulty_score": 3},
        ])
        self.assertEqual([m["exam_name"] for m in many], ["good", "poor"])
        self.assertEqual([m["rank"] for m in many], [1, 2])

    def test_study_match_is_between_0_and_1(self):
        self.assertTrue(0 <= study_match_score(1, 1, 1) <= 1.0)

    @unittest.skipUnless(HAVE_ML, "XGBoost / SHAP are not installed")
    def test_full_pipeline_and_shap_adds_up(self):
        from services.recommender import recommend
        from ml.explainability import explain_prediction_detailed

        result = recommend("B.Tech CSE", "Intermediate", 3,
                           "Quantitative Aptitude, Reasoning", age=21, target_exam="SSC CGL")
        self.assertTrue(result["recommendations"])
        top = result["recommendations"][0]
        self.assertEqual(top["rank"], 1)
        self.assertTrue(top["shap"])

        detail = explain_prediction_detailed("graduation", "advanced", 5, "Defence", "High", 0.8)
        total = detail["baseline"] + sum(c["impact"] for c in detail["contributions"])
        self.assertAlmostEqual(total, detail["prediction"], delta=0.01)


class BKTTests(unittest.TestCase):
    def test_default_parameters_unchanged(self):
        self.assertEqual(update_mastery(0.5, True), update_mastery(0.5, True, difficulty=None))

    def test_hard_correct_answer_is_worth_more_than_easy_correct(self):
        self.assertGreater(update_mastery(0.5, True, difficulty="Hard"),
                           update_mastery(0.5, True, difficulty="Easy"))


class StudyPlannerTests(unittest.TestCase):
    WEAK = [
        {"topic": "Percentages", "subject": "Quantitative Aptitude", "mastery": 0.10},
        {"topic": "Grammar", "subject": "English", "mastery": 0.30},
        {"topic": "Number Series", "subject": "Reasoning", "mastery": 0.35},
    ]
    NEW = [{"key": "a", "topic": "Algebra", "subject": "Quantitative Aptitude"},
           {"key": "b", "topic": "Geometry", "subject": "Quantitative Aptitude"}]

    def test_minutes_always_add_up_to_the_study_time(self):
        for hours in (0.5, 1, 1.5, 2, 3, 4, 6):
            plan = create_study_plan(hours, self.WEAK, "intermediate", self.NEW, ["Grammar"])
            self.assertEqual(sum(s["minutes"] for s in plan["sessions"]), plan["total_minutes"], hours)
            for day in plan["weekly_schedule"]:
                self.assertEqual(day["total_minutes"], plan["total_minutes"], (hours, day["day"]))

    def test_weak_sessions_respect_the_limits(self):
        plan = create_study_plan(6, self.WEAK, "beginner", self.NEW)
        for s in plan["sessions"]:
            if s["type"] == "weak":
                self.assertTrue(MIN_SESSION <= s["minutes"] <= MAX_SESSION)

    def test_weakest_topic_gets_most_time(self):
        plan = create_study_plan(3, self.WEAK, "intermediate", self.NEW)
        weak = {s["topic"]: s["minutes"] for s in plan["sessions"] if s["type"] == "weak"}
        self.assertGreaterEqual(weak["Percentages"], weak["Grammar"])
        self.assertGreaterEqual(weak["Grammar"], weak["Number Series"])

    def test_plan_contains_revision_practice_current_affairs(self):
        types = {s["type"] for s in create_study_plan(3, self.WEAK, "advanced", self.NEW)["sessions"]}
        self.assertTrue({"weak", "practice", "current_affairs", "revision"} <= types)

    def test_short_day_takes_only_the_weakest(self):
        plan = create_study_plan(1, self.WEAK, "beginner", [])
        weak = [s["topic"] for s in plan["sessions"] if s["type"] == "weak"]
        self.assertEqual(weak[0], "Percentages")
        self.assertLessEqual(len(weak), 3)

    def test_week_has_seven_days_and_sunday_is_revision(self):
        plan = create_study_plan(2, self.WEAK, "beginner", self.NEW)
        self.assertEqual(len(plan["weekly_schedule"]), 7)
        self.assertEqual(plan["weekly_schedule"][6]["focus"], "Revision & mixed practice")

    def test_no_weak_topics_still_gives_a_plan(self):
        plan = create_study_plan(2, [], "beginner")
        self.assertEqual(sum(s["minutes"] for s in plan["sessions"]), 120)

    def test_old_style_list_of_names_still_works(self):
        plan = create_study_plan(2, ["Percentages", "Grammar"], "beginner")
        self.assertTrue(any(s["topic"] == "Percentages" for s in plan["sessions"]))

    def test_zero_hours(self):
        self.assertEqual(create_study_plan(0, [], "beginner")["total_minutes"], 0)

    def test_allocate_minutes_total_and_limits(self):
        shares = allocate_minutes([0.9, 0.7, 0.65], 100)
        self.assertEqual(sum(shares), 100)
        self.assertTrue(all(MIN_SESSION <= s <= MAX_SESSION for s in shares))

    def test_times_are_in_order(self):
        sessions = create_study_plan(2, self.WEAK, "beginner")["sessions"]
        self.assertEqual((sessions[0]["time"], sessions[0]["period"]), ("9:00", "AM"))
        self.assertEqual(len({s["id"] for s in sessions}), len(sessions))

    def test_exam_code(self):
        self.assertEqual(exam_code_for("SSC CGL"), "CGL")
        self.assertIsNone(exam_code_for("UPSC"))
        self.assertIsNone(exam_code_for(None))


class DiagnosticTests(unittest.TestCase):
    def setUp(self):
        self.qmap = {int(q["question_id"]): q for q in load_questions()}
        self.diag = load_diagnostic_questions()

    def _answers(self, right_subjects):
        out = []
        for q in self.diag:
            if q["subject"] in right_subjects:
                out.append((int(q["question_id"]), q["correct_answer"]))
            else:
                out.append((int(q["question_id"]), "A" if q["correct_answer"] != "A" else "B"))
        return out

    def test_strong_and_weak_topics_are_found_with_subjects(self):
        result = analyse_answers(self._answers({"Quantitative Aptitude"}), self.qmap)
        by_topic = {t["topic"]: t for t in result["topic_results"]}
        self.assertEqual(by_topic["Percentages"]["status"], "Mastered")
        self.assertEqual(by_topic["Percentages"]["subject"], "Quantitative Aptitude")
        self.assertEqual(by_topic["Grammar"]["status"], "Weak")
        subjects = {s["subject"]: s for s in result["subject_analysis"]}
        self.assertEqual(subjects["Quantitative Aptitude"]["accuracy"], 100.0)
        self.assertEqual(subjects["General Intelligence & Reasoning"]["accuracy"], 0.0)

    def test_repeated_answer_to_one_question_counts_once(self):
        qid = int(self.diag[0]["question_id"])
        result = analyse_answers([(qid, "A"), (qid, self.diag[0]["correct_answer"])], self.qmap)
        self.assertEqual(result["answered"], 1)
        self.assertEqual(result["correct"], 1)

    def test_unknown_question(self):
        with self.assertRaises(QuestionNotFound):
            analyse_answers([(99999, "A")], self.qmap)


class FeedbackTests(unittest.TestCase):
    RECS = [
        {"exam_name": "SSC CGL", "suitability_score": 0.92, "reasons": ["Reason 1 (+10 pts)"],
         "explanation": [{"feature": "Study Time", "impact": 0.1, "effect": "positive"}]},
        {"exam_name": "Banking PO", "suitability_score": 0.85, "reasons": [], "explanation": []},
    ]

    def _feedback(self, **kwargs):
        base = dict(recommendations=self.RECS, target_exam="SSC CGL", topics=[], attempts=[],
                    diagnostic_weak=[], week_study_minutes=0, planned_week_minutes=0, has_diagnostic=False)
        base.update(kwargs)
        return build_feedback(**base)

    def test_new_student_is_asked_to_take_the_diagnostic(self):
        fb = self._feedback()
        self.assertTrue(any("diagnostic" in s.lower() for s in fb["next_steps"]))
        self.assertEqual(fb["reasons"], ["Reason 1 (+10 pts)"])

    def test_weakest_topic_is_named(self):
        topics = [{"topic": "Percentages", "subject": "Quant", "mastery": 0.2, "status": "Weak", "source": "diagnostic"},
                  {"topic": "Grammar", "subject": "English", "mastery": 0.8, "status": "Mastered", "source": "diagnostic"}]
        fb = self._feedback(topics=topics, has_diagnostic=True, diagnostic_weak=["Percentages"])
        self.assertIn("Percentages", fb["next_steps"][0])

    def test_recovered_topic_is_praised(self):
        topics = [{"topic": "Percentages", "subject": "Quant", "mastery": 0.6, "status": "Developing", "source": "quiz"}]
        fb = self._feedback(topics=topics, has_diagnostic=True, diagnostic_weak=["Percentages"])
        self.assertIn("moved out of your weak list", fb["feedback"])

    def test_target_exam_that_ranks_lower_is_flagged(self):
        fb = self._feedback(target_exam="Banking PO")
        self.assertTrue(any("ranks #2" in s for s in fb["next_steps"]))

    def test_no_recommendation(self):
        fb = self._feedback(recommendations=[])
        self.assertIn("profile", fb["next_steps"][0].lower())

    def test_steps_are_limited(self):
        self.assertLessEqual(len(self._feedback()["next_steps"]), 5)


class DashboardTests(unittest.TestCase):
    TODAY = date(2026, 11, 15)

    def test_streaks(self):
        days = {self.TODAY, self.TODAY - timedelta(days=1), self.TODAY - timedelta(days=2),
                self.TODAY - timedelta(days=10)}
        self.assertEqual(activity_streaks(days, self.TODAY), (3, 3))
        # streak is still alive when the student was active yesterday only
        self.assertEqual(activity_streaks({self.TODAY - timedelta(days=1)}, self.TODAY), (1, 1))
        self.assertEqual(activity_streaks({self.TODAY - timedelta(days=3)}, self.TODAY), (0, 1))
        self.assertEqual(activity_streaks(set(), self.TODAY), (0, 0))

    def test_stats_come_from_real_numbers(self):
        topics = [{"topic": "Percentages", "mastery": 0.3, "status": "Weak"},
                  {"topic": "Grammar", "mastery": 0.9, "status": "Mastered"}]
        attempts = [{"date": self.TODAY, "correct": True}, {"date": self.TODAY, "correct": False}]
        diagnostics = [{"date": self.TODAY, "total_answered": 24, "score_percentage": 50.0,
                        "weak_topics": ["Percentages"]}]
        minutes = {self.TODAY: 90, self.TODAY - timedelta(days=20): 60}
        result = compute_dashboard_stats(topics, attempts, diagnostics, minutes,
                                         {self.TODAY}, self.TODAY)
        stats = {s["id"]: s for s in result["stats"]}
        self.assertEqual(stats["progress"]["value"], "60")
        self.assertEqual(stats["accuracy"]["value"], "50")
        self.assertEqual(stats["solved"]["value"], "26")
        self.assertEqual(stats["time"]["value"], "2.5")
        self.assertEqual(stats["streak"]["value"], "1")
        ach = {a["label"]: a for a in result["achievements"]}
        self.assertTrue(ach["First Diagnostic"]["earned"])
        self.assertFalse(ach["Weak Topic Crusher"]["earned"])

    def test_empty_student(self):
        result = compute_dashboard_stats([], [], [], {}, set(), self.TODAY)
        stats = {s["id"]: s for s in result["stats"]}
        self.assertEqual(stats["solved"]["value"], "0")
        self.assertFalse(any(a["earned"] for a in result["achievements"]))


@unittest.skipUnless(HAVE_DB, "SQLAlchemy is not installed")
class DatabaseFlowTests(unittest.TestCase):
    """Saved study sessions -> study plan -> dashboard -> analytics."""

    def setUp(self):
        engine = create_engine("sqlite://")
        Base.metadata.create_all(engine)
        self.db = sessionmaker(bind=engine)()

        from services.syllabus_seed import seed_syllabus
        seed_syllabus(self.db)

        self.user = models.User(email="a@b.c", password_hash="x", full_name="Test Student")
        self.db.add(self.user)
        self.db.commit()
        self.student = models.Student(
            user_id=self.user.id, name="Test Student", qualification="B.Tech CSE", age=21,
            target_exam="SSC CGL", preparation_level="Intermediate", study_hours=3,
            interested_field="Administration / General",
            subject_preferences="Quantitative Aptitude, Reasoning, English",
        )
        self.db.add(self.student)
        self.db.commit()

    def tearDown(self):
        self.db.close()

    def _weak(self):
        from services.progress import save_topic_mastery
        save_topic_mastery(self.db, self.user.id, "Percentages", 0.15, "diagnostic", "Quantitative Aptitude")
        save_topic_mastery(self.db, self.user.id, "Grammar", 0.85, "diagnostic", "English")
        self.db.commit()

    def test_plan_uses_weak_topics_and_syllabus(self):
        from services.plan_builder import build_user_plan
        self._weak()
        plan = build_user_plan(self.db, self.user.id, 3, "Intermediate")
        types = {s["type"] for s in plan["sessions"]}
        self.assertIn("weak", types)
        self.assertIn("new", types)
        self.assertEqual(plan["weak_topics"], ["Percentages"])
        self.assertEqual(sum(s["minutes"] for s in plan["sessions"]), 180)
        self.assertEqual(plan["sessions"][0]["status"], "current")

    def test_ticking_a_session_is_saved_and_shown(self):
        from services import dates
        from services.plan_builder import build_user_plan
        from services.study_log import set_session_status, minutes_by_day

        plan = build_user_plan(self.db, self.user.id, 2, "Beginner")
        first = plan["sessions"][0]
        set_session_status(self.db, self.user.id, dates.today(), first["id"], first["topic"],
                           first["minutes"], True, first.get("syllabus_key"))
        self.db.commit()
        # print("SAVED SESSION:", self.db.query(models.StudySession).all())

        again = build_user_plan(self.db, self.user.id, 2, "Beginner")
        # print("REGENERATED SESSIONS:", again["sessions"])
        self.assertEqual(again["sessions"][0]["status"], "completed")
        self.assertEqual(minutes_by_day(self.db, self.user.id)[dates.today()], first["minutes"])

        # un-ticking removes it again
        set_session_status(self.db, self.user.id, dates.today(), first["id"], first["topic"],
                           first["minutes"], False, first.get("syllabus_key"))
        self.db.commit()
        self.assertEqual(minutes_by_day(self.db, self.user.id).get(dates.today(), 0), 0)

    def test_finishing_a_new_topic_ticks_the_syllabus(self):
        from services import dates
        from services.plan_builder import build_user_plan
        from services.study_log import set_session_status

        plan = build_user_plan(self.db, self.user.id, 3, "Beginner")
        new = next(s for s in plan["sessions"] if s["type"] == "new")
        set_session_status(self.db, self.user.id, dates.today(), new["id"], new["topic"],
                           new["minutes"], True, new["syllabus_key"])
        self.db.commit()
        self.assertEqual(self.db.query(models.SyllabusProgress).count(), 1)

        # the next plan moves on to a different syllabus topic
        later = build_user_plan(self.db, self.user.id, 3, "Beginner")
        self.assertNotIn(new["syllabus_key"], [s.get("syllabus_key") for s in later["sessions"]])

    def test_dashboard_and_analytics_for_new_and_active_student(self):
        from services.dashboard import build_dashboard
        from services.analytics import build_analytics
        from services.progress import save_topic_mastery

        empty = build_dashboard(self.db, self.user, self.student)
        self.assertEqual({s["id"] for s in empty["stats"]},
                         {"progress", "accuracy", "streak", "time", "solved"})
        self.assertTrue(empty["today"])

        self._weak()
        self.db.add(models.DiagnosticResult(user_id=self.user.id, total_answered=24, correct_answers=12,
                                            score_percentage=50.0, topic_analysis=[], weak_topics=["Percentages"]))
        self.db.add(models.QuizAttempt(user_id=self.user.id, question_id=1, topic="Percentages",
                                       difficulty="Easy", correct=True, mastery_before=0.15, mastery_after=0.4))
        self.db.commit()

        dash = build_dashboard(self.db, self.user, self.student)
        stats = {s["id"]: s for s in dash["stats"]}
        self.assertEqual(stats["solved"]["value"], "25")
        self.assertEqual(dash["student"]["streak"], 1)

        analytics = build_analytics(self.db, self.user.id)
        self.assertTrue(analytics["has_data"])
        self.assertIn("feedback", analytics)


if __name__ == "__main__":
    unittest.main()
