from pathlib import Path
import csv
import re


# Project root:
# Aspirixa_AI/
#     backend/
#     Dataset/
BASE_DIR = Path(__file__).resolve().parents[2]

DATASET_PATH = BASE_DIR / "Dataset" / "government_exams.csv"


# Qualification hierarchy
QUALIFICATION_LEVELS = {
    "10th": 1,
    "12th": 2,
    "diploma": 3,
    "graduation": 4,
    "postgraduation": 5,
}

QUALIFICATION_LABELS = {
    "10th": "10th Pass",
    "12th": "12th Pass",
    "diploma": "Diploma",
    "graduation": "Graduation",
    "postgraduation": "Postgraduation",
}

# Short names of master's degrees (after removing dots and spaces)
_MASTERS = ("msc", "mtech", "mcom", "mba", "mca", "mphil", "phd")


def normalize_qualification(qualification: str) -> str:
    """
    Converts the different qualification names used by the app
    (B.Tech CSE, B.Sc, 12th Pass, Postgraduate ...) into one of:
    10th, 12th, diploma, graduation, postgraduation.
    """

    value = (qualification or "").lower().strip()
    compact = re.sub(r"[^a-z0-9]", "", value)

    if not compact:
        return ""

    if ("post" in value and "grad" in value) or "master" in value:
        return "postgraduation"

    if compact.startswith(_MASTERS) or compact in ("ma", "me"):
        return "postgraduation"

    if "diploma" in value:
        return "diploma"

    if "12" in value or "intermediate" in value or "hsc" in compact:
        return "12th"

    if "10" in value or "matric" in value:
        return "10th"

    if "graduat" in value or "degree" in value or "bachelor" in value:
        return "graduation"

    # B.Tech, B.E., B.Sc, B.Com, B.A., BCA, BBA ...
    if compact.startswith("b"):
        return "graduation"

    return value


def load_exams():
    """
    Loads government exam information from CSV.
    """

    exams = []

    with open(DATASET_PATH, mode="r", encoding="utf-8") as file:
        reader = csv.DictReader(file)

        for row in reader:
            exams.append(row)

    return exams


def _level(qualification: str) -> int:
    return QUALIFICATION_LEVELS.get(
        normalize_qualification(qualification),
        0
    )


def is_eligible(student_qualification: str, exam_requirement: str) -> bool:
    """
    Qualification-based filtering.
    A higher qualification always satisfies a lower requirement.
    """

    return _level(student_qualification) >= _level(exam_requirement)


def _to_int(value):
    try:
        return int(str(value).strip())
    except (TypeError, ValueError):
        return None


def check_exam(student_qualification: str, exam: dict, age=None) -> dict:
    """
    Applies the eligibility rules of ONE exam (qualification and age)
    and explains the result in plain words.

    Returns {"eligible": bool, "reasons": [str]}
    """

    reasons = []

    student_level = _level(student_qualification)
    required_level = _level(exam["minimum_qualification"])
    required_label = QUALIFICATION_LABELS.get(
        normalize_qualification(exam["minimum_qualification"]),
        exam["minimum_qualification"]
    )

    if student_level == 0:
        reasons.append("Your qualification was not recognised.")
    elif student_level < required_level:
        reasons.append(f"Requires {required_label} or higher.")

    if age not in (None, ""):
        try:
            age = int(age)
        except (TypeError, ValueError):
            age = None

    if age is not None:
        min_age = _to_int(exam.get("min_age"))
        max_age = _to_int(exam.get("max_age"))

        if min_age is not None and age < min_age:
            reasons.append(f"Minimum age is {min_age} (you are {age}).")

        if max_age is not None and age > max_age:
            reasons.append(
                f"Maximum age is {max_age} for General category (you are {age})."
            )

    return {"eligible": not reasons, "reasons": reasons}


def evaluate_exams(student_qualification: str, age=None):
    """
    Checks EVERY exam and returns it with its eligibility result,
    so the screen can also show why an exam was filtered out.
    """

    results = []

    for exam in load_exams():
        check = check_exam(student_qualification, exam, age)
        results.append({**exam, **check})

    return results


def get_eligible_exams(student_qualification: str, age=None):
    """
    Returns examinations for which the student satisfies the
    qualification (and, when given, age) rules of the dataset.

    These are indicative rules. The official notification of each exam
    (category relaxations, specific degrees) is the final authority.
    """

    return [
        exam
        for exam in evaluate_exams(student_qualification, age)
        if exam["eligible"]
    ]
