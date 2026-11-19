"""
Module 1 + Module 6 (explanation part): the full exam-recommendation pipeline.

    Eligibility rules -> XGBoost suitability -> TOPSIS ranking -> SHAP explanation

Used by the /recommendation route, the dashboard and the feedback service,
so all three always agree. The scoring helpers at the top are plain
Python and can be tested without XGBoost or SHAP installed.
"""
from services.eligibility import (
    evaluate_exams,
    normalize_qualification,
    QUALIFICATION_LABELS,
    QUALIFICATION_LEVELS,
)


# ----------------------------------------------------------------------
# Subjects
# ----------------------------------------------------------------------
# Exam subjects in the dataset use different names. They are mapped to the
# four subjects the student can choose in the profile.
QUANT = "Quantitative Aptitude"
REASON = "Reasoning"
ENGLISH = "English"
GA = "General Awareness"

SUBJECT_ALIASES = {
    "quantitative aptitude": [QUANT],
    "mathematics": [QUANT],
    "reasoning": [REASON],
    "csat": [REASON, QUANT],
    "english": [ENGLISH],
    "general awareness": [GA],
    "general knowledge": [GA],
    "general studies": [GA],
    "current affairs": [GA],
    "general science": [GA],
}

# "Preferred Field" on the profile -> exam domain in the dataset
FIELD_TO_DOMAIN = {
    "administration / general": "General",
    "banking & finance": "Banking",
    "railways": "Railways",
    "defence": "Defence",
}

# Names used in the "Target exam" drop-down -> exam name in the dataset
TARGET_ALIASES = {
    "upsc": "upsc cse",
    "railway ntpc": "rrb ntpc",
}

LEVEL_VALUE = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0}
NEED_VALUE = {"low": 0.0, "medium": 0.5, "high": 1.0}


def canonical_subjects(names):
    """['Mathematics', 'Reasoning'] -> {'Quantitative Aptitude', 'Reasoning'}"""
    result = set()

    for name in names or []:
        key = str(name).strip().lower()
        result.update(SUBJECT_ALIASES.get(key, []))

    return result


def split_subjects(text):
    if not text:
        return []
    if isinstance(text, (list, tuple)):
        return [str(s).strip() for s in text if str(s).strip()]
    separator = ";" if ";" in text else ","
    return [part.strip() for part in text.split(separator) if part.strip()]


def subject_alignment(preferred_subjects, exam_subjects):
    """
    How well the student's preferred subjects fit the exam syllabus (0 to 1).
    Balances two questions: does the exam cover what the student likes, and
    does the student like what the exam needs? (harmonic mean of both)
    """
    preferred = canonical_subjects(preferred_subjects)
    exam = canonical_subjects(exam_subjects)

    if not preferred or not exam:
        return 0.5

    overlap = len(preferred & exam)

    if overlap == 0:
        return 0.0

    coverage_of_exam = overlap / len(exam)
    coverage_of_choice = overlap / len(preferred)

    return round(
        2 * coverage_of_exam * coverage_of_choice
        / (coverage_of_exam + coverage_of_choice),
        3
    )


def field_alignment(field, exam_domain):
    domain = FIELD_TO_DOMAIN.get((field or "").strip().lower())

    if domain is None:
        return 0.5
    if domain == exam_domain:
        return 1.0
    if exam_domain == "General":
        return 0.6
    return 0.3


def target_alignment(target_exam, exam_name):
    if not target_exam:
        return 0.5

    target = TARGET_ALIASES.get(target_exam.strip().lower(), target_exam.strip().lower())

    return 1.0 if target == exam_name.strip().lower() else 0.0


def study_match_score(subject_fit, field_fit, target_fit):
    """Preference match used as a TOPSIS benefit criterion (0 to 1)."""
    return round(0.6 * subject_fit + 0.25 * field_fit + 0.15 * target_fit, 3)


def qualification_fit(qualification, required):
    """
    1.0 when the qualification is exactly what the exam asks for. Each
    extra level above the requirement lowers it by 0.25 (a graduate is
    allowed to write a 10th-level exam, but it is rarely the best match).
    """
    have = QUALIFICATION_LEVELS.get(normalize_qualification(qualification), 0)
    need = QUALIFICATION_LEVELS.get(normalize_qualification(required), 0)

    if have < need or have == 0:
        return 0.0

    return max(0.25, round(1.0 - 0.25 * (have - need), 2))


def exam_factors(exam, qualification, level, hours, subject_fit):
    """
    The four bars shown for every exam (0-100). Each is a plain,
    explainable rule on the profile - they are NOT model outputs.
    """
    recommended = float(exam.get("recommended_hours") or 3)

    need = NEED_VALUE.get(exam["difficulty"].lower(), 0.5)
    have = LEVEL_VALUE.get((level or "beginner").lower(), 0.0)

    level_score = 100 if have >= need else round(100 - (need - have) * 60)

    return {
        "qualification": round(
            qualification_fit(qualification, exam["minimum_qualification"]) * 100
        ),
        "subject": round(subject_fit * 100),
        "time": min(100, round(float(hours) / recommended * 100)),
        "level": level_score,
    }


# ----------------------------------------------------------------------
# Plain-language reasons from SHAP
# ----------------------------------------------------------------------
def _reason(item, profile, exam):
    key = item["key"]
    positive = item["impact"] > 0
    points = abs(round(item["impact"] * 100))

    hours = profile["study_hours"]
    needed = exam.get("recommended_hours")

    if key == "qualification":
        qualification = QUALIFICATION_LABELS.get(
            normalize_qualification(profile["qualification"]), profile["qualification"]
        )
        return (
            f"Your qualification ({qualification}) suits this exam"
            if positive else
            f"Your qualification ({qualification}) is a weaker fit for this exam"
        )
    if key == "preparation_level":
        return (
            f"Your {profile['preparation_level'].lower()} preparation level matches the difficulty ({exam['difficulty']})"
            if positive else
            f"Your {profile['preparation_level'].lower()} preparation level makes a {exam['difficulty'].lower()}-difficulty exam harder"
        )
    if key == "study_hours":
        return (
            f"{hours:g} hour(s) of daily study fits the roughly {needed} hours this exam needs"
            if positive else
            f"{hours:g} hour(s) of daily study is below the roughly {needed} hours this exam needs"
        )
    if key == "subject_match":
        return (
            "Your preferred subjects line up with this exam's syllabus"
            if positive else
            "Your preferred subjects only partly match this exam's syllabus"
        )
    if key == "domain":
        return (
            f"The {exam['domain']} domain fits your profile"
            if positive else
            f"The {exam['domain']} domain is less aligned with your profile"
        )
    if key == "difficulty":
        return (
            f"{exam['difficulty']} difficulty is manageable for you"
            if positive else
            f"{exam['difficulty']} difficulty lowers your suitability"
        )
    return f"{item['feature']} changed the score by {points} points"


def build_reasons(contributions, profile, exam, limit=4):
    reasons = []

    for item in contributions[:limit]:
        text = _reason(item, profile, exam)
        sign = "+" if item["impact"] > 0 else "-"
        reasons.append(f"{text} ({sign}{abs(round(item['impact'] * 100))} pts)")

    return reasons


def build_summary_text(exam_name, suitability, reasons):
    if not reasons:
        return f"{exam_name} has a suitability of {round(suitability * 100)}% for your profile."

    return (
        f"{exam_name} is a {round(suitability * 100)}% match for your profile. "
        + "; ".join(reasons[:3]) + "."
    )


# ----------------------------------------------------------------------
# Pipeline
# ----------------------------------------------------------------------
def recommend(
    qualification,
    preparation_level,
    study_hours,
    subject_preferences=None,
    age=None,
    field=None,
    target_exam=None,
):
    # Imported here so the helpers above work without the ML libraries
    from ml.xgboost_model import predict_suitability
    from ml.topsis import topsis_rank, difficulty_to_score
    from ml.explainability import explain_prediction_detailed

    subjects = split_subjects(subject_preferences)

    # 1. Eligibility rules (every exam is checked, the reason is kept)
    checked = evaluate_exams(qualification, age)

    eligibility = [
        {
            "exam_id": int(exam["exam_id"]),
            "exam_name": exam["exam_name"],
            "domain": exam["domain"],
            "difficulty": exam["difficulty"],
            "eligible": exam["eligible"],
            "reasons": exam["reasons"],
        }
        for exam in checked
    ]

    eligible = [exam for exam in checked if exam["eligible"]]

    profile = {
        "qualification": qualification,
        "normalized_qualification": normalize_qualification(qualification),
        "age": age,
        "preparation_level": preparation_level,
        "study_hours": float(study_hours),
        "subject_preferences": ", ".join(subjects) if subjects else None,
        "subjects": subjects,
        "field": field,
        "target_exam": target_exam,
    }

    if not eligible:
        return {
            "student_profile": profile,
            "eligibility": eligibility,
            "recommendations": [],
            "baseline": None,
        }

    # 2. XGBoost suitability
    candidates = []
    by_id = {}

    for exam in eligible:
        subject_fit = subject_alignment(subjects, split_subjects(exam["subjects"]))

        prediction = predict_suitability(
            qualification=qualification,
            preparation_level=preparation_level,
            study_hours=study_hours,
            domain=exam["domain"],
            difficulty=exam["difficulty"],
            subject_match=subject_fit,
        )

        by_id[int(exam["exam_id"])] = (exam, subject_fit)

        candidates.append({
            "exam_id": int(exam["exam_id"]),
            "exam_name": exam["exam_name"],
            "suitability_score": prediction["suitability_score"],
            "study_match": study_match_score(
                subject_fit,
                field_alignment(field, exam["domain"]),
                target_alignment(target_exam, exam["exam_name"]),
            ),
            "qualification_fit": qualification_fit(
                qualification, exam["minimum_qualification"]
            ),
            "difficulty_score": difficulty_to_score(exam["difficulty"]),
        })

    # 3. TOPSIS multi-criteria ranking
    ranked = topsis_rank(candidates)

    # 4. SHAP explanation for every ranked exam
    recommendations = []
    baseline = None

    for row in ranked:
        exam, subject_fit = by_id[row["exam_id"]]

        detail = explain_prediction_detailed(
            qualification=qualification,
            preparation_level=preparation_level,
            study_hours=study_hours,
            domain=exam["domain"],
            difficulty=exam["difficulty"],
            subject_match=subject_fit,
        )

        baseline = detail["baseline"]

        reasons = build_reasons(detail["contributions"], profile, exam)

        recommendations.append({
            "rank": row["rank"],
            "exam_id": row["exam_id"],
            "exam_name": exam["exam_name"],
            "body": exam.get("conducting_body") or "",
            "domain": exam["domain"],
            "difficulty": exam["difficulty"],
            "subjects": exam["subjects"],
            "suitability_score": row["suitability_score"],
            "topsis_score": round(float(row["topsis_score"]), 3),
            "match_score": round(float(row["study_match"]) * 100),
            "factors": exam_factors(
                {**exam, "eligible": True},
                qualification, preparation_level, study_hours, subject_fit,
            ),
            # SHAP contributions (percentage points of suitability)
            "explanation": [
                {"feature": c["feature"], "impact": c["impact"], "effect": c["effect"]}
                for c in detail["contributions"]
            ],
            "shap": [
                {"label": c["feature"], "value": c["impact"]}
                for c in detail["contributions"][:6]
            ],
            "reasons": reasons,
            "explanation_text": build_summary_text(
                exam["exam_name"], row["suitability_score"], reasons
            ),
        })

    return {
        "student_profile": profile,
        "eligibility": eligibility,
        "recommendations": recommendations,
        "baseline": baseline,
    }
