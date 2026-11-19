from services.eligibility import get_eligible_exams


eligible_exams = get_eligible_exams("B.Tech CSE")

print("\nEligible Exams:\n")

for exam in eligible_exams:
    print(
        f"{exam['exam_name']} "
        f"({exam['minimum_qualification']})"
    )