"""
Builds the numbers for the Performance page from what the student really did.

compute_analytics() works on plain lists/dicts (easy to test).
build_analytics() reads those lists from the database.
Nothing here is made up: if there is no data, the page shows an empty state.
"""
from datetime import date, timedelta

SHORT_SUBJECT = {
    "Quantitative Aptitude": "Quant",
    "General Intelligence & Reasoning": "Reasoning",
    "English Language": "English",
    # old labels, kept so topic-mastery rows saved before Step 1 still display
    "Reasoning": "Reasoning",
    "English": "English",
    "General Awareness": "GA",
}
DIFFICULTIES = ["Easy", "Medium", "Hard"]


def _percent(value):
    return round(float(value) * 100)


def compute_analytics(topics, attempts, diagnostics, today=None, study_minutes_by_day=None, next_steps=None):
    """
    topics:      [{"topic", "subject", "mastery" (0-1), "status"}]
    attempts:    [{"date" (date), "difficulty", "correct" (bool)}]
    diagnostics: [{"total_answered", "correct_answers", "score_percentage"}]  newest first
    study_minutes_by_day: {date: completed study minutes}   (optional)
    next_steps:  plain-text suggestions from the feedback module   (optional)
    """
    today = today or date.today()
    study_minutes_by_day = study_minutes_by_day or {}

    quiz_total = len(attempts)
    quiz_correct = sum(1 for a in attempts if a["correct"])
    diagnostic_total = sum(d["total_answered"] for d in diagnostics)

    has_data = bool(topics or attempts or diagnostics)

    # ---- summary cards ----
    if quiz_total:
        accuracy = round(quiz_correct * 100 / quiz_total)
        accuracy_note = f"{quiz_correct} of {quiz_total} quiz answers correct"
    elif diagnostics:
        accuracy = round(diagnostics[0]["score_percentage"])
        accuracy_note = "From your latest diagnostic test"
    else:
        accuracy, accuracy_note = 0, "No answers yet"

    if topics:
        overall = round(sum(t["mastery"] for t in topics) * 100 / len(topics))
        mastery_note = f"Average of {len(topics)} topics"
    else:
        overall, mastery_note = 0, "Take the diagnostic test first"

    summary = [
        {"id": "acc", "label": "Accuracy", "value": str(accuracy), "unit": "%",
         "trend": accuracy_note, "tone": "green"},
        {"id": "mastery", "label": "Overall Mastery", "value": str(overall), "unit": "%",
         "trend": mastery_note, "tone": "blue"},
        {"id": "solved", "label": "Questions Solved", "value": str(quiz_total + diagnostic_total), "unit": "",
         "trend": f"{quiz_total} quiz + {diagnostic_total} diagnostic", "tone": "purple"},
    ]

    # ---- weekly quiz accuracy (only days that have answers) ----
    days = [today - timedelta(days=offset) for offset in range(6, -1, -1)]
    weekly_labels, weekly_values = [], []
    for day in days:
        day_attempts = [a for a in attempts if a["date"] == day]
        if day_attempts:
            right = sum(1 for a in day_attempts if a["correct"])
            weekly_labels.append(day.strftime("%a %d"))
            weekly_values.append(round(right * 100 / len(day_attempts)))

    # ---- mastery by subject ----
    by_subject = {}
    for t in topics:
        by_subject.setdefault(t["subject"] or "Other", []).append(t["mastery"])
    subjects = [
        {"name": name, "short": SHORT_SUBJECT.get(name, name),
         "value": _percent(sum(values) / len(values))}
        for name, values in by_subject.items()
    ]

    # ---- quiz questions by difficulty ----
    difficulty = [
        {"label": level, "value": sum(1 for a in attempts if a["difficulty"] == level)}
        for level in DIFFICULTIES
    ]

    # ---- topic list (weakest first) ----
    topic_rows = [
        {"name": t["topic"], "subject": SHORT_SUBJECT.get(t["subject"], t["subject"] or ""),
         "value": _percent(t["mastery"])}
        for t in sorted(topics, key=lambda t: (t["mastery"], t["topic"]))
    ]

    # ---- trend analysis: latest quiz days against the days before ----
    daily_accuracy = []
    for day in sorted({a["date"] for a in attempts}):
        day_attempts = [a for a in attempts if a["date"] == day]
        daily_accuracy.append(
            sum(1 for a in day_attempts if a["correct"]) * 100 / len(day_attempts)
        )
    trend = None
    if len(daily_accuracy) >= 2:
        latest = daily_accuracy[-1]
        before = sum(daily_accuracy[:-1]) / len(daily_accuracy[:-1])
        change = round(latest - before)
        trend = {"change": change, "direction": "up" if change > 0 else "down" if change < 0 else "flat"}

    # ---- study time (hours completed in the last 7 days) ----
    week_start = today - timedelta(days=6)
    week_minutes = sum(m for d, m in study_minutes_by_day.items() if d >= week_start)

    # ---- insights: plain rules on the real numbers ----
    insights = []
    if topic_rows:
        weakest = topic_rows[0]
        insights.append(f"{weakest['name']} is your weakest topic ({weakest['value']}%). Practise it first.")
        strongest = topic_rows[-1]
        if strongest["value"] >= 70 and strongest["name"] != weakest["name"]:
            insights.append(f"{strongest['name']} is your strongest topic ({strongest['value']}%).")
        weak_count = sum(1 for t in topics if t["status"] == "Weak")
        if weak_count:
            insights.append(f"{weak_count} topic(s) are marked Weak. Your study plan gives them extra time.")
    if quiz_total:
        insights.append(f"You answered {quiz_correct} of {quiz_total} adaptive-quiz questions correctly.")
    else:
        insights.append("Take the adaptive quiz to start tracking how you improve.")
    if trend and trend["direction"] != "flat":
        word = "improved" if trend["direction"] == "up" else "dropped"
        insights.append(f"Your latest quiz day {word} by {abs(trend['change'])} points compared with your earlier average.")
    if week_minutes:
        insights.append(f"You completed {week_minutes / 60:.1f} study hours in the last 7 days.")
    for step in next_steps or []:
        insights.append(f"Next step: {step}")

    return {
        "has_data": has_data,
        "summary": summary,
        "weekly": {"labels": weekly_labels, "values": weekly_values},
        "subjects": subjects,
        "difficulty": difficulty,
        "topics": topic_rows,
        "insights": insights,
        "trend": trend,
        "study_hours_week": round(week_minutes / 60, 1),
    }


def build_analytics(db, user_id):
    # Imported here so compute_analytics() can be tested without SQLAlchemy
    from database.models import DiagnosticResult, QuizAttempt, TopicMastery
    from services import dates
    from services.study_log import minutes_by_day

    topics = [
        {"topic": r.topic, "subject": r.subject, "mastery": r.mastery, "status": r.status}
        for r in db.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
    ]
    attempts = [
        {"date": dates.to_local_date(r.created_at), "difficulty": r.difficulty, "correct": r.correct}
        for r in db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id).all()
    ]
    diagnostics = [
        {"total_answered": r.total_answered, "correct_answers": r.correct_answers,
         "score_percentage": r.score_percentage}
        for r in (
            db.query(DiagnosticResult)
            .filter(DiagnosticResult.user_id == user_id)
            .order_by(DiagnosticResult.id.desc())
            .all()
        )
    ]

    # Module 6 feedback: the next steps become part of the learning insights
    feedback = None
    try:
        from services.feedback import build_feedback_for_user
        feedback = build_feedback_for_user(db, user_id)
    except Exception as error:
        print(f"Analytics: feedback unavailable ({error})")

    result = compute_analytics(
        topics, attempts, diagnostics,
        study_minutes_by_day=minutes_by_day(db, user_id),
        next_steps=feedback["next_steps"][:2] if feedback else None,
    )
    result["feedback"] = feedback
    return result
