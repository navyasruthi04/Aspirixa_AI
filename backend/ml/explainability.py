from functools import lru_cache

import numpy as np
import shap

from ml.xgboost_model import encode, load_model


# One-hot columns are added back together so the student sees
# "Qualification" and not "qualification_graduation".
GROUP_LABELS = {
    "qualification": "Qualification",
    "preparation_level": "Preparation Level",
    "study_hours": "Study Time",
    "subject_match": "Subject Alignment",
    "domain": "Exam Domain",
    "difficulty": "Exam Difficulty",
}


def _group_of(feature):
    for group in GROUP_LABELS:
        if feature == group or feature.startswith(group + "_"):
            return group
    return feature


@lru_cache(maxsize=1)
def _explainer():
    return shap.TreeExplainer(load_model()["model"])


def _sigmoid(x):
    return 1.0 / (1.0 + np.exp(-x))


def explain_prediction_detailed(
    qualification,
    preparation_level,
    study_hours,
    domain,
    difficulty,
    subject_match=0.5
):
    """
    SHAP explanation of one suitability prediction.

    SHAP values from XGBoost are in log-odds. They are converted into
    percentage-point contributions so that

        baseline + sum(contributions) = predicted suitability

    which is much easier for a student to read.
    """

    saved = load_model()
    model = saved["model"]
    features = saved["features"]

    input_data = encode([{
        "qualification": qualification,
        "preparation_level": preparation_level,
        "study_hours": study_hours,
        "domain": domain,
        "difficulty": difficulty,
        "subject_match": subject_match
    }])

    explainer = _explainer()

    shap_values = explainer.shap_values(input_data)

    # XGBoost binary classification: one row of log-odds values
    if isinstance(shap_values, list):
        values = np.asarray(shap_values[-1])[0]
    else:
        values = np.asarray(shap_values)[0]

    expected = float(np.ravel(explainer.expected_value)[-1])

    log_odds_total = float(values.sum())
    baseline = float(_sigmoid(expected))
    prediction = float(_sigmoid(expected + log_odds_total))

    # Share of the probability change that belongs to each log-odds unit
    scale = (
        (prediction - baseline) / log_odds_total
        if abs(log_odds_total) > 1e-9
        else 0.0
    )

    grouped = {}

    for feature, value in zip(features, values):
        group = _group_of(feature)
        grouped[group] = grouped.get(group, 0.0) + float(value)

    contributions = []

    for group, log_odds in grouped.items():
        impact = log_odds * scale

        if abs(impact) < 0.0005:
            continue

        contributions.append({
            "feature": GROUP_LABELS.get(group, group),
            "key": group,
            "impact": round(impact, 4),
            "log_odds": round(log_odds, 4),
            "effect": "positive" if impact > 0 else "negative"
        })

    contributions.sort(key=lambda item: abs(item["impact"]), reverse=True)

    return {
        "baseline": round(baseline, 4),
        "prediction": round(prediction, 4),
        "contributions": contributions
    }


def explain_prediction(
    qualification,
    preparation_level,
    study_hours,
    domain,
    difficulty,
    subject_match=0.5
):
    return explain_prediction_detailed(
        qualification,
        preparation_level,
        study_hours,
        domain,
        difficulty,
        subject_match
    )["contributions"]
