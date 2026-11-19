from ml.explainability import explain_prediction


result = explain_prediction(
    qualification="graduation",
    preparation_level="intermediate",
    study_hours=4,
    domain="General",
    difficulty="Medium"
)

print("\nSHAP Explanation:\n")

for item in result:
    print(
        f"{item['feature']} -> "
        f"{item['effect']} impact "
        f"({item['impact']})"
    )