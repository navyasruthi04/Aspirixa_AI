from services.bkt import update_mastery, classify_topic
from services.question_bank import available_topics, next_question


def get_target_difficulty(mastery):
    if mastery < 0.40:
        return "Easy"

    if mastery < 0.70:
        return "Medium"

    return "Hard"


def choose_topic(mastery_by_topic, answered_question_ids=None, default_mastery=0.5):
    """
    Picks the topic the student needs most: the one with the LOWEST mastery
    that still has an unanswered question. Topics the student has not
    practised yet start at default_mastery.
    Returns (topic, mastery), or (None, None) when no question is left.

    The list of topics with an unanswered question comes from the database
    (SQL), in the order of each topic's first question, so ties are broken the
    same way as before.
    """
    available = {
        topic: mastery_by_topic.get(topic, default_mastery)
        for topic in available_topics(answered_question_ids)
    }

    if not available:
        return None, None

    topic = min(available, key=available.get)
    return topic, available[topic]


def get_next_question(
    topic,
    mastery,
    answered_question_ids=None
):
    if answered_question_ids is None:
        answered_question_ids = []

    target_difficulty = get_target_difficulty(mastery)

    # SQL picks the first unused question of this topic at the target difficulty;
    # if there is none, any unused question of the same topic.
    question = next_question(topic, target_difficulty, answered_question_ids)

    if not question:
        return None

    return {
        "question_id": int(question["question_id"]),
        "topic": question["topic"],
        "difficulty": question["difficulty"],
        "question": question["question"],
        "options": {
            "A": question["option_a"],
            "B": question["option_b"],
            "C": question["option_c"],
            "D": question["option_d"]
        },
        "mastery_probability": mastery,
        "mastery_status": classify_topic(mastery)
    }


def process_answer(
    mastery,
    correct,
    difficulty=None
):
    updated_mastery = update_mastery(
        mastery_probability=mastery,
        correct=correct,
        difficulty=difficulty
    )

    next_difficulty = get_target_difficulty(
        updated_mastery
    )

    return {
        "previous_mastery": mastery,
        "updated_mastery": updated_mastery,
        "status": classify_topic(updated_mastery),
        "next_difficulty": next_difficulty
    }