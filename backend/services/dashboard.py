"""
Home dashboard numbers, built from what the student really did.

compute_dashboard_stats() is plain Python (easy to test);
build_dashboard() reads the data from the database.
"""
from datetime import timedelta


def activity_streaks(active_days, today):
    """
    active_days: set of dates on which the student did something
    (quiz, diagnostic or a completed study session).
    Returns (current_streak, longest_streak).
    A streak is still "alive" if the student was active yesterday.
    """
    if not active_days:
        return 0, 0

    # current streak
    cursor = today if today in active_days else today - timedelta(days=1)
    current = 0
    while cursor in active_days:
        current += 1
        cursor -= timedelta(days=1)

    # longest streak
    longest = 0
    for day in active_days:
        if day - timedelta(days=1) in active_days:
            continue                      # not the start of a run
        length = 0
        cursor = day
        while cursor in active_days:
            length += 1
            cursor += timedelta(days=1)
        longest = max(longest, length)

    return current, longest


def compute_dashboard_stats(topics, attempts, diagnostics, minutes_by_day, active_days, today):
    """
    topics:        [{"topic","mastery" (0-1),"status"}]
    attempts:      [{"date","correct"}]
    diagnostics:   [{"date","total_answered","score_percentage","weak_topics"}] newest first
    minutes_by_day:{date: completed study minutes}
    """
    week_start = today - timedelta(days=6)

    quiz_total = len(attempts)
    quiz_correct = sum(1 for a in attempts if a["correct"])
    diagnostic_total = sum(d["total_answered"] for d in diagnostics)
    solved = quiz_total + diagnostic_total
    solved_week = sum(1 for a in attempts if a["date"] >= week_start) + sum(
        d["total_answered"] for d in diagnostics if d["date"] >= week_start
    )

    # progress = average topic mastery
    if topics:
        progress = round(sum(t["mastery"] for t in topics) * 100 / len(topics))
        progress_note = f"Average of {len(topics)} topics"
    else:
        progress, progress_note = 0, "Take the diagnostic test first"

    # accuracy
    if quiz_total:
        accuracy = round(quiz_correct * 100 / quiz_total)
        accuracy_note = f"{quiz_correct} of {quiz_total} quiz answers correct"
    elif diagnostics:
        accuracy = round(diagnostics[0]["score_percentage"])
        accuracy_note = "From your latest diagnostic test"
    else:
        accuracy, accuracy_note = 0, "No answers yet"

    # streak
    current, longest = activity_streaks(active_days, today)
    streak_note = (
        f"Your longest so far: {longest} days" if current
        else "Study today to start a streak"
    )

    # study time
    total_minutes = sum(minutes_by_day.values())
    week_minutes = sum(m for d, m in minutes_by_day.items() if d >= week_start)

    stats = [
        {"id": "progress", "label": "Overall Progress", "value": str(progress), "unit": "%",
         "trend": progress_note, "tone": "primary"},
        {"id": "accuracy", "label": "Quiz Accuracy", "value": str(accuracy), "unit": "%",
         "trend": accuracy_note, "tone": "green"},
        {"id": "streak", "label": "Study Streak", "value": str(current), "unit": " Days",
         "trend": streak_note, "tone": "amber"},
        {"id": "time", "label": "Study Time", "value": f"{total_minutes / 60:.1f}", "unit": " hrs",
         "trend": f"{week_minutes / 60:.1f} hrs in the last 7 days", "tone": "blue"},
        {"id": "solved", "label": "Questions Solved", "value": str(solved), "unit": "",
         "trend": f"{solved_week} in the last 7 days", "tone": "primary"},
    ]

    # achievements
    diag_weak = (diagnostics[-1]["weak_topics"] if diagnostics else []) or []
    # the diagnostic list is newest first, so the FIRST diagnostic is the last item
    status_now = {t["topic"]: t["status"] for t in topics}
    crushed = sum(1 for name in diag_weak if status_now.get(name) and status_now[name] != "Weak")

    window = [today - timedelta(days=i) for i in range(14)]
    consistency = round(sum(1 for d in window if d in active_days) * 100 / 14)

    achievements = [
        {"id": "a1", "label": "First Diagnostic",
         "note": "Completed" if diagnostics else "Not taken yet", "earned": bool(diagnostics)},
        {"id": "a2", "label": "7-Day Streak",
         "note": "Completed" if longest >= 7 else f"{min(current, 7)} of 7 days", "earned": longest >= 7},
        {"id": "a3", "label": "100 Questions",
         "note": "Completed" if solved >= 100 else f"{solved} of 100", "earned": solved >= 100},
        {"id": "a4", "label": "Weak Topic Crusher",
         "note": f"{crushed} of {len(diag_weak)} topics" if diag_weak else "Take the diagnostic first",
         "earned": bool(diag_weak) and crushed == len(diag_weak)},
        {"id": "a5", "label": "Consistency Champion",
         "note": f"{consistency} of 90%", "earned": consistency >= 90},
    ]

    return {"stats": stats, "achievements": achievements, "streak": current}


def build_dashboard(db, user, student):
    from database.models import DiagnosticResult, QuizAttempt, TopicMastery
    from services import dates
    from services.plan_builder import build_user_plan
    from services.study_log import minutes_by_day

    today = dates.today()

    topics = [
        {"topic": r.topic, "mastery": r.mastery, "status": r.status}
        for r in db.query(TopicMastery).filter(TopicMastery.user_id == user.id).all()
    ]
    attempts = [
        {"date": dates.to_local_date(r.created_at), "correct": r.correct}
        for r in db.query(QuizAttempt).filter(QuizAttempt.user_id == user.id).all()
    ]
    diagnostics = [
        {"date": dates.to_local_date(r.created_at), "total_answered": r.total_answered,
         "score_percentage": r.score_percentage, "weak_topics": r.weak_topics}
        for r in db.query(DiagnosticResult)
        .filter(DiagnosticResult.user_id == user.id)
        .order_by(DiagnosticResult.id.desc()).all()
    ]
    minutes = minutes_by_day(db, user.id)

    active = {a["date"] for a in attempts} | {d["date"] for d in diagnostics} | set(minutes)

    result = compute_dashboard_stats(topics, attempts, diagnostics, minutes, active, today)

    # ---- today's sessions ----
    hours = (student.study_hours if student else 0) or 2
    level = (student.preparation_level if student else "Beginner") or "Beginner"
    plan = build_user_plan(db, user.id, hours, level)

    # ---- top recommendation ----
    recommendation = None

    if student is not None and student.qualification:
        try:
            from services.recommender import recommend

            reco = recommend(
                qualification=student.qualification,
                preparation_level=student.preparation_level,
                study_hours=student.study_hours or 1,
                subject_preferences=student.subject_preferences,
                age=student.age,
                field=student.interested_field,
                target_exam=student.target_exam,
            )
            if reco["recommendations"]:
                top = reco["recommendations"][0]
                recommendation = {
                    "id": top["exam_id"],
                    "name": top["exam_name"],
                    "body": top["body"],
                    "suitability": round(top["suitability_score"] * 100),
                    "factors": top["factors"],
                    "explanation": top["explanation_text"],
                }
        except Exception as error:
            print(f"Dashboard: recommendation unavailable ({error})")

    return {
        "student": {
            "fullName": (student.name if student else None) or user.full_name,
            "streak": result["streak"],
        },
        "stats": result["stats"],
        "recommendation": recommendation,
        "today": plan.get("sessions", []),
        "achievements": result["achievements"],
    }
