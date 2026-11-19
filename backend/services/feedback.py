"""
Module 6: explainable recommendation + personalised feedback.

build_feedback() is plain Python: it turns the numbers the system already has
(recommendation + SHAP reasons, topic mastery, quiz results, study time)
into reasons, next steps and a short feedback message. Every sentence comes
from a rule on real data, so nothing is invented.
"""

MAX_STEPS = 5


def _accuracy(attempts):
    if not attempts:
        return None
    return round(sum(1 for a in attempts if a["correct"]) * 100 / len(attempts))


def build_feedback(
    recommendations,        # list from recommender.recommend()["recommendations"]
    target_exam,            # profile target exam name or None
    topics,                 # [{"topic","subject","mastery","status","source"}]
    attempts,               # quiz attempts, oldest first: [{"correct": bool, ...}]
    diagnostic_weak,        # weak topics at the latest diagnostic
    week_study_minutes,
    planned_week_minutes,
    has_diagnostic,
):
    steps = []
    notes = []

    top = recommendations[0] if recommendations else None

    # ---------- explanation of the recommendation ----------
    reasons = top["reasons"] if top else []
    factors = top["explanation"] if top else []

    if top is None:
        steps.append("Complete your profile (qualification, age, preparation level and study hours) to get an exam recommendation.")
    else:
        names = [r["exam_name"].lower() for r in recommendations]
        if target_exam:
            alias = {"upsc": "upsc cse", "railway ntpc": "rrb ntpc"}
            wanted = alias.get(target_exam.strip().lower(), target_exam.strip().lower())
            if wanted in names:
                position = names.index(wanted) + 1
                if position == 1:
                    notes.append(f"Your target exam, {top['exam_name']}, is also your top recommendation.")
                else:
                    mine = recommendations[position - 1]
                    steps.append(
                        f"Your target {mine['exam_name']} ranks #{position} for you "
                        f"({round(mine['suitability_score'] * 100)}% suitability). "
                        f"{top['exam_name']} ranks first, so compare both before you commit."
                    )

    # ---------- diagnostic and weak topics ----------
    weakest = sorted(
        [t for t in topics if t["status"] == "Weak"], key=lambda t: t["mastery"]
    )

    if not has_diagnostic:
        steps.append("Take the diagnostic test so Aspirixa AI can find your weak topics.")
    elif weakest:
        first = weakest[0]
        steps.append(
            f"Start with {first['topic']} (mastery {round(first['mastery'] * 100)}%). "
            "Short adaptive quizzes on it will raise your mastery fastest."
        )
        if len(weakest) > 1:
            others = ", ".join(t["topic"] for t in weakest[1:3])
            steps.append(f"Then work on {others}; your study plan already gives weak topics extra time.")
    else:
        steps.append("No weak topics right now. Raise the difficulty with adaptive quizzes and revise regularly.")

    # ---------- topics already improved ----------
    recovered = [
        t["topic"] for t in topics
        if t["topic"] in (diagnostic_weak or []) and t["status"] != "Weak"
    ]
    if recovered:
        notes.append(
            f"Well done: {', '.join(recovered[:3])} moved out of your weak list since the diagnostic."
        )

    # ---------- quiz performance ----------
    if has_diagnostic:
        if len(attempts) < 10:
            steps.append(
                f"Answer at least {10 - len(attempts)} more adaptive-quiz questions so the mastery estimates become reliable."
            )
        else:
            overall = _accuracy(attempts)
            recent = _accuracy(attempts[-5:])
            earlier = _accuracy(attempts[-10:-5])

            if recent is not None and earlier is not None:
                if recent - earlier >= 10:
                    notes.append(f"Your recent quiz accuracy ({recent}%) is up from {earlier}%.")
                elif earlier - recent >= 10:
                    steps.append(
                        f"Your recent quiz accuracy ({recent}%) dropped from {earlier}%. Revise the last topics you studied before new questions."
                    )

            if overall is not None and overall < 50:
                steps.append("Your overall quiz accuracy is below 50%. Revisit the concepts of your weak topics before attempting more questions.")

    # ---------- study time ----------
    if planned_week_minutes > 0:
        done = week_study_minutes
        if done == 0:
            steps.append("Tick the sessions of your study plan as you finish them so your study time is tracked.")
        elif done < 0.5 * planned_week_minutes:
            steps.append(
                f"You completed {round(done / 60, 1)} of {round(planned_week_minutes / 60, 1)} planned study hours this week. Try to finish at least one more session each day."
            )
        elif done >= 0.8 * planned_week_minutes:
            notes.append(f"You completed {round(done / 60, 1)} of {round(planned_week_minutes / 60, 1)} planned study hours this week.")

    steps = steps[:MAX_STEPS]

    headline = (
        f"Recommended exam: {top['exam_name']} ({round(top['suitability_score'] * 100)}% suitability)"
        if top else "Complete your profile to receive a recommendation"
    )

    message_parts = notes[:2] + steps[:2]

    return {
        "headline": headline,
        "reasons": reasons,
        "contributing_factors": factors,
        "next_steps": steps,
        "feedback": " ".join(message_parts) if message_parts else "Keep practising regularly.",
    }


def build_feedback_for_user(db, user_id):
    """Reads the saved data of one student and returns build_feedback()."""
    from datetime import timedelta

    from database.models import DiagnosticResult, QuizAttempt, Student, TopicMastery
    from services import dates
    from services.study_log import minutes_by_day

    student = (
        db.query(Student).filter(Student.user_id == user_id).order_by(Student.id.desc()).first()
    )

    recommendations = []

    if student is not None and student.qualification:
        try:
            from services.recommender import recommend

            recommendations = recommend(
                qualification=student.qualification,
                preparation_level=student.preparation_level,
                study_hours=student.study_hours or 1,
                subject_preferences=student.subject_preferences,
                age=student.age,
                field=student.interested_field,
                target_exam=student.target_exam,
            )["recommendations"]
        except Exception as error:   # ML libraries missing / model problem
            print(f"Feedback: recommendation unavailable ({error})")

    topics = [
        {"topic": r.topic, "subject": r.subject, "mastery": r.mastery,
         "status": r.status, "source": r.source}
        for r in db.query(TopicMastery).filter(TopicMastery.user_id == user_id).all()
    ]

    attempts = [
        {"correct": r.correct}
        for r in db.query(QuizAttempt).filter(QuizAttempt.user_id == user_id)
        .order_by(QuizAttempt.id).all()
    ]

    latest = (
        db.query(DiagnosticResult)
        .filter(DiagnosticResult.user_id == user_id)
        .order_by(DiagnosticResult.id.desc())
        .first()
    )

    today = dates.today()
    week_start = today - timedelta(days=6)
    week_minutes = sum(
        minutes for day, minutes in minutes_by_day(db, user_id).items() if day >= week_start
    )

    planned = round((student.study_hours or 0) * 60 * 7) if student is not None else 0

    return build_feedback(
        recommendations=recommendations,
        target_exam=student.target_exam if student is not None else None,
        topics=topics,
        attempts=attempts,
        diagnostic_weak=(latest.weak_topics if latest is not None else []) or [],
        week_study_minutes=week_minutes,
        planned_week_minutes=planned,
        has_diagnostic=latest is not None,
    )
