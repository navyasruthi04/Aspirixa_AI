"""Module 2: BKT analysis of a diagnostic attempt (no database, no web framework)."""
from services.bkt import update_mastery, classify_topic


class QuestionNotFound(Exception):
    pass


def analyse_answers(answers, question_map):
    # answers: [(question_id, "A"/"B"/"C"/"D"), ...]
    """
    Pure BKT analysis of one diagnostic attempt (no database).

    For every topic, mastery starts at 50% and is updated after each answer
    (harder questions are guessed less and slipped on more - see bkt.py).
    Returns the topic results plus subject-level performance.
    """

    # One answer per question, in question order, so the result is repeatable
    latest = {}
    for question_id, chosen in answers:
        latest[question_id] = chosen

    mastery_by_topic = {}
    subject_by_topic = {}
    stats_by_topic = {}
    correct_count = 0

    for question_id in sorted(latest):

        question = question_map.get(question_id)

        if not question:
            raise QuestionNotFound(f"Question {question_id} not found.")

        topic = question["topic"]
        subject_by_topic[topic] = question["subject"]

        # Start each topic at 50% mastery
        mastery_by_topic.setdefault(topic, 0.50)
        stats_by_topic.setdefault(topic, {"correct": 0, "total": 0})

        correct = (
            latest[question_id].upper()
            == question["correct_answer"].upper()
        )

        stats_by_topic[topic]["total"] += 1

        if correct:
            correct_count += 1
            stats_by_topic[topic]["correct"] += 1

        mastery_by_topic[topic] = update_mastery(
            mastery_probability=mastery_by_topic[topic],
            correct=correct,
            difficulty=question["difficulty"]
        )

    topic_results = []

    for topic, mastery in mastery_by_topic.items():

        topic_results.append({
            "topic": topic,
            "subject": subject_by_topic[topic],
            "mastery_probability": mastery,
            "status": classify_topic(mastery),
            "correct": stats_by_topic[topic]["correct"],
            "total": stats_by_topic[topic]["total"],
        })

    # Subject-level performance (average topic mastery + accuracy)
    subjects = {}
    for result in topic_results:
        entry = subjects.setdefault(
            result["subject"],
            {"subject": result["subject"], "mastery": [], "correct": 0, "total": 0}
        )
        entry["mastery"].append(result["mastery_probability"])
        entry["correct"] += result["correct"]
        entry["total"] += result["total"]

    subject_analysis = [
        {
            "subject": entry["subject"],
            "mastery_probability": round(sum(entry["mastery"]) / len(entry["mastery"]), 4),
            "accuracy": round(entry["correct"] * 100 / entry["total"], 1),
            "correct": entry["correct"],
            "total": entry["total"],
        }
        for entry in subjects.values()
    ]

    return {
        "answered": len(latest),
        "correct": correct_count,
        "topic_results": topic_results,
        "subject_analysis": subject_analysis,
    }
