from ml.topsis import (
    topsis_rank,
    difficulty_to_score,
    calculate_study_match
)


exams = [
    {
        "exam_name": "SSC CGL",
        "suitability_score": 0.85,
        "study_match": calculate_study_match(
            "General",
            "General"
        ),
        "difficulty_score": difficulty_to_score("Medium")
    },
    {
        "exam_name": "Banking PO",
        "suitability_score": 0.78,
        "study_match": calculate_study_match(
            "General",
            "Banking"
        ),
        "difficulty_score": difficulty_to_score("Medium")
    },
    {
        "exam_name": "UPSC CSE",
        "suitability_score": 0.60,
        "study_match": calculate_study_match(
            "General",
            "General"
        ),
        "difficulty_score": difficulty_to_score("High")
    },
]


results = topsis_rank(exams)

print("\nTOPSIS Ranking:\n")

for exam in results:
    print(
        f"{exam['rank']}. "
        f"{exam['exam_name']} - "
        f"TOPSIS Score: {exam['topsis_score']:.3f}"
    )