from services.bkt import (
    update_mastery,
    classify_topic
)


mastery = 0.50

answers = [
    True,
    False,
    False,
    True,
    False
]

print("\nBKT Mastery Tracking:\n")

for index, answer in enumerate(answers, start=1):

    mastery = update_mastery(
        mastery_probability=mastery,
        correct=answer
    )

    status = classify_topic(mastery)

    print(
        f"Question {index}: "
        f"{'Correct' if answer else 'Wrong'} | "
        f"Mastery: {mastery} | "
        f"Status: {status}"
    )