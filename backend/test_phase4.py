import unittest
from services.syllabus_data import SYLLABUS, OFFICIAL_SOURCES, EXAM_NAMES


class SyllabusCatalogueTests(unittest.TestCase):
    def test_catalogue_has_cgl_and_chsl(self):
        self.assertEqual(set(EXAM_NAMES), {row["exam_code"] for row in SYLLABUS})

    def test_every_topic_has_stable_key_and_subtopics(self):
        keys = [row["key"] for row in SYLLABUS]
        self.assertEqual(len(keys), len(set(keys)))
        for row in SYLLABUS:
            self.assertTrue(row["key"])
            self.assertTrue(row["tier"])
            self.assertTrue(row["subject"])
            self.assertTrue(row["topic"])
            self.assertIsInstance(row["subtopics"], list)
            self.assertGreater(len(row["subtopics"]), 0)

    def test_required_exam_tiers_exist(self):
        tiers = {(row["exam_code"], row["tier"]) for row in SYLLABUS}
        for expected in {
            ("CGL", "Tier 1"), ("CGL", "Tier 2 Paper I"),
            ("CGL", "Tier 2 Paper II"), ("CGL", "Tier 2 Paper III"),
            ("CHSL", "Tier 1"), ("CHSL", "Tier 2"),
        }:
            self.assertIn(expected, tiers)

    def test_official_notice_links_are_configured(self):
        self.assertIn("ssc.gov.in", OFFICIAL_SOURCES["CGL"])
        self.assertIn("ssc.gov.in", OFFICIAL_SOURCES["CHSL"])


if __name__ == "__main__":
    unittest.main()

    def test_all_nine_ssc_exams_have_syllabus(self):
        codes = {row["exam_code"] for row in SYLLABUS}
        for expected in ["CGL", "CHSL", "MTS", "GD", "CPO", "JE", "STENO", "SELECTION_POST", "JHT"]:
            self.assertIn(expected, codes)

    def test_je_has_three_engineering_branches(self):
        tiers = {row["tier"] for row in SYLLABUS if row["exam_code"] == "JE"}
        for expected in ["Paper I", "Paper II Civil", "Paper II Electrical", "Paper II Mechanical"]:
            self.assertIn(expected, tiers)

    def test_every_exam_with_a_syllabus_has_a_display_name(self):
        for row in SYLLABUS:
            self.assertIn(row["exam_code"], EXAM_NAMES)
