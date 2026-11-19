from ml.xgboost_model import predict_suitability


result = predict_suitability(
    qualification="graduation",
    preparation_level="intermediate",
    study_hours=4,
    domain="General",
    difficulty="Medium"
)

print("\nXGBoost Prediction:")
print(result)