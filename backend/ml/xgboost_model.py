from functools import lru_cache
from pathlib import Path

import joblib
import numpy as np
import pandas as pd

from services.eligibility import normalize_qualification


BASE_DIR = Path(__file__).resolve().parents[2]

MODEL_DIR = BASE_DIR / "backend" / "ml"
MODEL_PATH = MODEL_DIR / "xgboost_exam_model.pkl"

# Change this number whenever the features or the training data change.
# A saved model with a different version is retrained automatically.
MODEL_VERSION = "2"


# ----------------------------------------------------------------------
# Features
# ----------------------------------------------------------------------
CATEGORIES = {
    "qualification": ["10th", "12th", "diploma", "graduation", "postgraduation"],
    "preparation_level": ["beginner", "intermediate", "advanced"],
    "domain": ["General", "Banking", "Railways", "Defence", "Technical"],
    "difficulty": ["Low", "Medium", "High"],
}

NUMERIC_FEATURES = ["study_hours", "subject_match"]

FEATURES = NUMERIC_FEATURES + [
    f"{column}_{value}"
    for column, values in CATEGORIES.items()
    for value in values
]


def encode(rows):
    """
    Turns a list of profile dictionaries into the model's feature table.
    The columns are always the same, in the same order, so a single
    prediction can never lose a column (the old get_dummies approach could).
    """

    table = []

    for row in rows:
        record = {name: 0.0 for name in FEATURES}

        record["study_hours"] = float(row["study_hours"])
        record["subject_match"] = float(row.get("subject_match", 0.5))

        for column in CATEGORIES:
            value = str(row[column])

            if column == "qualification":
                value = normalize_qualification(value)
            elif column == "preparation_level":
                value = value.lower().strip()
            else:
                value = value.strip().capitalize() if value.strip().lower() in (
                    "low", "medium", "high"
                ) else value.strip()

            key = f"{column}_{value}"

            if key in record:
                record[key] = 1.0

        table.append(record)

    return pd.DataFrame(table, columns=FEATURES)


# ----------------------------------------------------------------------
# Prototype training data
# ----------------------------------------------------------------------
# A real labelled "which exam suits which aspirant" dataset does not exist
# publicly. For this prototype the training table is GENERATED from a
# readiness rule (preparation level, study time against what the exam
# needs, subject match, qualification) plus random noise. XGBoost learns
# this pattern and returns a probability, which TOPSIS and SHAP then use.
# In the report, describe the dataset as synthetic / prototype data.
REQUIRED_HOURS = {"Low": 2.0, "Medium": 3.5, "High": 5.5}
PASS_MARK = {"Low": 0.48, "Medium": 0.58, "High": 0.70}
LEVEL_VALUE = {"beginner": 0.0, "intermediate": 0.5, "advanced": 1.0}


def build_training_data(rows=1500, seed=42):
    rng = np.random.RandomState(seed)

    records = []

    for _ in range(rows):
        qualification = rng.choice(CATEGORIES["qualification"])
        level = rng.choice(CATEGORIES["preparation_level"])
        domain = rng.choice(CATEGORIES["domain"])
        difficulty = rng.choice(CATEGORIES["difficulty"])
        hours = int(rng.randint(1, 7))
        subject_match = float(np.round(rng.uniform(0.2, 1.0), 2))

        qualification_value = (
            CATEGORIES["qualification"].index(qualification) + 1
        ) / 5

        readiness = (
            0.35 * LEVEL_VALUE[level]
            + 0.30 * min(hours / REQUIRED_HOURS[difficulty], 1.0)
            + 0.25 * subject_match
            + 0.10 * qualification_value
            + rng.normal(0, 0.04)
        )

        records.append({
            "qualification": qualification,
            "preparation_level": level,
            "domain": domain,
            "difficulty": difficulty,
            "study_hours": hours,
            "subject_match": subject_match,
            "suitability": int(readiness >= PASS_MARK[difficulty]),
        })

    return pd.DataFrame(records)


# ----------------------------------------------------------------------
# Training / loading
# ----------------------------------------------------------------------
def train_model():
    from sklearn.metrics import accuracy_score
    from sklearn.model_selection import train_test_split
    from xgboost import XGBClassifier

    data = build_training_data()

    X = encode(data.drop(columns="suitability").to_dict("records"))
    y = data["suitability"]

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )

    model = XGBClassifier(
        n_estimators=120,
        max_depth=3,
        learning_rate=0.1,
        random_state=42,
        eval_metric="logloss"
    )

    model.fit(X_train, y_train)

    accuracy = float(accuracy_score(y_test, model.predict(X_test)))

    # Final model uses all the rows
    model.fit(X, y)

    MODEL_DIR.mkdir(parents=True, exist_ok=True)

    joblib.dump(
        {
            "model": model,
            "features": list(X.columns),
            "version": MODEL_VERSION,
            "test_accuracy": round(accuracy, 3),
        },
        MODEL_PATH
    )

    load_model.cache_clear()

    print("XGBoost model trained successfully!")
    print(f"Held-out accuracy: {accuracy:.3f}")
    print(f"Model saved at: {MODEL_PATH}")


@lru_cache(maxsize=1)
def load_model():
    """
    Loads the saved model. If the file is missing, damaged or from an
    older version, the model is trained again (takes about a second).
    """

    saved = None

    if MODEL_PATH.exists():
        try:
            saved = joblib.load(MODEL_PATH)
        except Exception:
            saved = None

    if (
        not isinstance(saved, dict)
        or saved.get("version") != MODEL_VERSION
        or saved.get("features") != FEATURES
    ):
        train_model()
        saved = joblib.load(MODEL_PATH)

    return saved


def ensure_model():
    """Called when the server starts so the first request is not slow."""
    return load_model()


def predict_suitability(
    qualification,
    preparation_level,
    study_hours,
    domain,
    difficulty,
    subject_match=0.5
):

    saved = load_model()

    model = saved["model"]

    input_data = encode([{
        "qualification": qualification,
        "preparation_level": preparation_level,
        "study_hours": study_hours,
        "domain": domain,
        "difficulty": difficulty,
        "subject_match": subject_match
    }])

    probability = float(model.predict_proba(input_data)[0][1])

    prediction = int(probability >= 0.5)

    return {
        "suitable": bool(prediction),
        "suitability_score": round(probability, 3)
    }


if __name__ == "__main__":
    train_model()
