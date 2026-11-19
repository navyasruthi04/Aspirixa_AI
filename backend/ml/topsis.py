import numpy as np
import pandas as pd


def topsis_rank(exams):
    """
    Rank eligible exams using TOPSIS.

    Criteria:
    - suitability_score: benefit  (XGBoost probability)
    - study_match: benefit        (subject / field / target preference)
    - qualification_fit: benefit  (optional - how closely the qualification
                                   matches what the exam asks for)
    - difficulty_score: cost
    """

    if not exams:
        return []

    df = pd.DataFrame(exams)

    if "qualification_fit" in df.columns:
        criteria = [
            "suitability_score",
            "study_match",
            "qualification_fit",
            "difficulty_score"
        ]
        weights = np.array([0.40, 0.25, 0.20, 0.15])
        benefit = [True, True, True, False]
    else:
        criteria = [
            "suitability_score",
            "study_match",
            "difficulty_score"
        ]
        weights = np.array([0.5, 0.3, 0.2])
        benefit = [True, True, False]

    matrix = df[criteria].astype(float).values

    # Step 1: Normalize decision matrix
    denominator = np.sqrt((matrix ** 2).sum(axis=0))
    denominator[denominator == 0] = 1.0   # avoid dividing by zero
    normalized = matrix / denominator

    # Step 2: Apply criteria weights
    weighted = normalized * weights

    # Step 3: Determine ideal best and worst
    # (benefit criteria: higher is better, cost criteria: lower is better)
    maximum = weighted.max(axis=0)
    minimum = weighted.min(axis=0)

    ideal_best = np.where(benefit, maximum, minimum)
    ideal_worst = np.where(benefit, minimum, maximum)

    # Step 4: Calculate distances
    distance_best = np.sqrt(
        ((weighted - ideal_best) ** 2).sum(axis=1)
    )

    distance_worst = np.sqrt(
        ((weighted - ideal_worst) ** 2).sum(axis=1)
    )

    # Step 5: TOPSIS closeness score
    total_distance = distance_best + distance_worst

    # With a single exam (or identical exams) both distances are 0
    topsis_score = np.where(
        total_distance == 0,
        1.0,
        distance_worst / np.where(total_distance == 0, 1.0, total_distance)
    )

    df["topsis_score"] = topsis_score

    # Higher TOPSIS score = closer to ideal solution
    df = df.sort_values(
        by="topsis_score",
        ascending=False
    ).reset_index(drop=True)

    df["rank"] = df.index + 1

    return df.to_dict(orient="records")


def difficulty_to_score(difficulty):
    mapping = {
        "Low": 1,
        "Medium": 2,
        "High": 3
    }

    return mapping.get(difficulty, 2)


def calculate_study_match(
    preferred_domain,
    exam_domain
):
    if not preferred_domain:
        return 0.5

    if preferred_domain.lower() == exam_domain.lower():
        return 1.0

    if exam_domain.lower() == "general":
        return 0.7

    return 0.4