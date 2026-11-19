# Harder questions are guessed less often and slipped on more often.
# difficulty=None keeps the original parameters.
DIFFICULTY_PARAMETERS = {
    "easy": {"slip": 0.05, "guess": 0.25},
    "medium": {"slip": 0.10, "guess": 0.20},
    "hard": {"slip": 0.15, "guess": 0.15},
}


def update_mastery(
    mastery_probability,
    correct,
    learn_probability=0.20,
    slip_probability=0.10,
    guess_probability=0.20,
    difficulty=None
):
    """
    Bayesian Knowledge Tracing update.

    mastery_probability:
        Current probability that the student has mastered the topic.

    correct:
        True if the student answered correctly.

    difficulty:
        Optional "Easy" / "Medium" / "Hard" - changes the slip and
        guess probabilities of this question.
    """

    if difficulty:
        params = DIFFICULTY_PARAMETERS.get(str(difficulty).lower())

        if params:
            slip_probability = params["slip"]
            guess_probability = params["guess"]

    # Probability of answering correctly
    probability_correct = (
        mastery_probability * (1 - slip_probability)
        + (1 - mastery_probability) * guess_probability
    )

    if correct:
        posterior = (
            mastery_probability * (1 - slip_probability)
        ) / probability_correct
    else:
        probability_incorrect = 1 - probability_correct

        posterior = (
            mastery_probability * slip_probability
        ) / probability_incorrect

    # Learning transition
    updated_mastery = (
        posterior
        + (1 - posterior) * learn_probability
    )

    return round(updated_mastery, 4)


def classify_topic(mastery_probability):
    """
    Classify topic based on mastery probability.
    """

    if mastery_probability < 0.40:
        return "Weak"

    if mastery_probability < 0.70:
        return "Developing"

    return "Mastered"