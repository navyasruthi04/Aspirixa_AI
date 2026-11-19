"""
Module 3: constraint-based personalised study plan.

Inputs  : daily study time, weak topics (with mastery), preparation level,
          syllabus topics still to cover, revision requirement.
Output  : today's schedule, a 7-day schedule and the time allocation.

Constraints used when the minutes are shared out
  * the minutes of all sessions add up to exactly the daily study time
  * revision, practice and current affairs get a reserved share
  * every weak-topic session gets at least MIN_SESSION and at most
    MAX_SESSION minutes (very weak topics get more, weighted by weakness)
  * if the time is too short for all weak topics, the weakest are taken
    first and the others are rotated into the other days of the week

This module is plain Python (no database), so it is easy to test.
"""
from datetime import date as _date
from typing import Dict, List, Optional

STEP = 5            # minutes are given in blocks of 5
MIN_SESSION = 10    # shortest useful topic session
MAX_SESSION = 60    # longest single topic session
START_HOUR = 9      # the day's schedule starts at 9:00 AM

# Share of the day reserved for revision, by preparation level
REVISION_SHARE = {"beginner": 0.15, "intermediate": 0.20, "advanced": 0.25}
PRACTICE_SHARE = 0.20
WEAK_SHARE_OF_LEARNING = 0.70

DAY_NAMES = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


# ----------------------------------------------------------------------
# helpers
# ----------------------------------------------------------------------
def _round_step(value: float) -> int:
    return int(round(value / STEP) * STEP)


def _normalise_weak_topics(weak_topics) -> List[Dict]:
    """Accepts ['Percentages'] or [{'topic', 'subject', 'mastery'}]."""
    result = []

    for item in weak_topics or []:
        if isinstance(item, str):
            result.append({"topic": item, "subject": None, "mastery": None})
        else:
            result.append({
                "topic": item["topic"],
                "subject": item.get("subject"),
                "mastery": item.get("mastery"),
            })

    # weakest first (unknown mastery counts as 0.3)
    result.sort(key=lambda t: (t["mastery"] if t["mastery"] is not None else 0.3, t["topic"]))
    return result


def allocate_minutes(weights: List[float], budget: int,
                     minimum: int = MIN_SESSION, maximum: int = MAX_SESSION) -> List[int]:
    """
    Shares `budget` minutes between items in proportion to `weights`,
    keeping every share between `minimum` and `maximum` (water-filling).
    The result is in blocks of STEP and adds up to the budget whenever
    the limits allow it.
    """
    count = len(weights)

    if count == 0 or budget <= 0:
        return [0] * count

    # Not enough time to give everyone the minimum: caller should have
    # reduced the number of items. Share equally as a safe fallback.
    if count * minimum > budget:
        base = _round_step(budget / count)
        return [base] * count

    shares = [0.0] * count
    free = set(range(count))
    remaining = float(budget)

    while free:
        total_weight = sum(weights[i] for i in free) or 1.0
        trial = {i: remaining * weights[i] / total_weight for i in free}

        low = [i for i in free if trial[i] < minimum]
        high = [i for i in free if trial[i] > maximum]

        if not low and not high:
            for i in free:
                shares[i] = trial[i]
            break

        for i in low:
            shares[i] = minimum
            remaining -= minimum
            free.discard(i)
        for i in high:
            if i in free:
                shares[i] = maximum
                remaining -= maximum
                free.discard(i)

    blocks = [max(minimum, min(maximum, _round_step(x))) for x in shares]

    # Put the rounding difference on the item with the most room
    difference = budget - sum(blocks)
    order = sorted(range(count), key=lambda i: -weights[i])

    for i in order * 20:
        if difference == 0:
            break
        move = STEP if difference > 0 else -STEP
        if minimum <= blocks[i] + move <= maximum:
            blocks[i] += move
            difference -= move

    return blocks


def _clock(minutes_from_start: int):
    total = START_HOUR * 60 + minutes_from_start
    hour24, minute = divmod(total, 60)
    hour24 %= 24
    period = "AM" if hour24 < 12 else "PM"
    hour12 = hour24 % 12 or 12
    return f"{hour12}:{minute:02d}", period


def _resource(kind: str, topic: str) -> str:
    if kind == "weak":
        return f"Revise the concept notes of {topic}, then solve 15 targeted practice questions."
    if kind == "new":
        return f"Read the syllabus notes for {topic} and solve 10 basic questions."
    if kind == "practice":
        return "Take an adaptive quiz: questions follow your current mastery."
    if kind == "current_affairs":
        return "Read a daily current-affairs digest and attempt a short quiz."
    return f"Quick revision of: {topic}. Re-attempt questions you got wrong earlier."


# ----------------------------------------------------------------------
# one day
# ----------------------------------------------------------------------
def build_day(
    total_minutes: int,
    weak: List[Dict],
    preparation_level: str,
    new_topics: Optional[List[Dict]] = None,
    revision_topics: Optional[List[str]] = None,
    revision_day: bool = False,
) -> List[Dict]:
    """Builds the sessions of ONE day (not yet timed)."""

    level = (preparation_level or "beginner").lower()
    new_topics = new_topics or []
    revision_topics = revision_topics or []

    if revision_day:
        # Weekly revision day: no new learning, revise + mixed practice
        revision = _round_step(total_minutes * 0.45)
        current = 15 if total_minutes >= 90 else (10 if total_minutes >= 45 else 0)
        practice = total_minutes - revision - current
        learning = 0
    else:
        revision = _round_step(total_minutes * REVISION_SHARE.get(level, 0.20))
        current = 15 if total_minutes >= 90 else (10 if total_minutes >= 45 else 0)
        practice = _round_step(total_minutes * PRACTICE_SHARE)
        learning = total_minutes - revision - current - practice

    sessions: List[Dict] = []

    if learning > 0:
        weak_budget = _round_step(learning * WEAK_SHARE_OF_LEARNING) if weak else 0
        if not new_topics and weak:
            weak_budget = learning               # nothing else to learn: use it all
        fresh_budget = learning - weak_budget

        # --- weak topics ---
        if weak and weak_budget >= MIN_SESSION:
            take = min(len(weak), max(1, weak_budget // MIN_SESSION))
            chosen = weak[:take]
            weights = [
                max(0.1, 1.0 - (t["mastery"] if t["mastery"] is not None else 0.3))
                for t in chosen
            ]
            minutes = allocate_minutes(weights, weak_budget)
            for topic, mins in zip(chosen, minutes):
                sessions.append({
                    "type": "weak", "topic": topic["topic"],
                    "subject": topic["subject"] or topic["topic"],
                    "minutes": mins, "priority": "High", "weak": True,
                    "resource": _resource("weak", topic["topic"]),
                })
        else:
            fresh_budget += weak_budget          # too little time for a weak session

        # --- new syllabus topics ---
        if new_topics and fresh_budget >= MIN_SESSION:
            take = min(len(new_topics), max(1, fresh_budget // 15), 2)
            chosen = new_topics[:take]
            minutes = allocate_minutes([1.0] * len(chosen), fresh_budget, minimum=MIN_SESSION, maximum=45)
            leftover = fresh_budget - sum(minutes)
            for topic, mins in zip(chosen, minutes):
                sessions.append({
                    "type": "new", "topic": topic["topic"],
                    "subject": topic.get("subject") or topic["topic"],
                    "minutes": mins, "priority": "Medium", "weak": False,
                    "syllabus_key": topic.get("key"),
                    "resource": _resource("new", topic["topic"]),
                })
            practice += max(0, leftover)
        else:
            practice += max(0, fresh_budget)

    if practice > 0:
        sessions.append({
            "type": "practice", "topic": "Mixed practice (adaptive quiz)", "subject": "Practice",
            "minutes": practice, "priority": "Medium", "weak": False,
            "resource": _resource("practice", ""),
        })

    if current > 0:
        sessions.append({
            "type": "current_affairs", "topic": "Current Affairs", "subject": "General Awareness",
            "minutes": current, "priority": "Medium", "weak": False,
            "resource": _resource("current_affairs", ""),
        })

    if revision > 0:
        names = ", ".join(revision_topics[:3]) if revision_topics else "your recent topics"
        sessions.append({
            "type": "revision", "topic": "Previously learned topics", "subject": "Revision",
            "minutes": revision, "priority": "High", "weak": False,
            "resource": _resource("revision", names),
        })

    # The totals must match the daily time exactly
    difference = total_minutes - sum(s["minutes"] for s in sessions)
    if sessions and difference:
        sessions[-2 if len(sessions) > 1 else -1]["minutes"] += difference

    return sessions


def _add_times(sessions: List[Dict]) -> List[Dict]:
    offset = 0
    for index, session in enumerate(sessions):
        session["time"], session["period"] = _clock(offset)
        session["id"] = f"{session['type']}:{session['topic']}"
        offset += session["minutes"]
    return sessions


# ----------------------------------------------------------------------
# full plan
# ----------------------------------------------------------------------
def create_study_plan(
    study_hours: float,
    weak_topics,
    preparation_level: str,
    new_topics: Optional[List[Dict]] = None,
    revision_topics: Optional[List[str]] = None,
) -> Dict:

    total_minutes = _round_step(study_hours * 60)

    if total_minutes <= 0:
        return {
            "total_minutes": 0,
            "sessions": [],
            "message": "Study hours must be greater than 0."
        }

    weak = _normalise_weak_topics(weak_topics)
    new_topics = list(new_topics or [])

    # ---- today ----
    sessions = _add_times(build_day(
        total_minutes, weak, preparation_level, new_topics, revision_topics
    ))

    # ---- 7-day schedule: weak topics rotate, Sunday is revision day ----
    weekly = []
    per_day = max(1, min(len(weak), max(1, (_round_step(total_minutes * 0.5)) // MIN_SESSION))) if weak else 0
    new_cursor = 0

    for day_index, day_name in enumerate(DAY_NAMES):
        is_revision_day = day_index == 6

        if weak:
            start = (day_index * per_day) % len(weak)
            rotated = (weak[start:] + weak[:start])
        else:
            rotated = []

        fresh = new_topics[new_cursor:new_cursor + 2] if not is_revision_day else []
        if fresh:
            new_cursor += len(fresh)

        day_sessions = build_day(
            total_minutes, rotated, preparation_level, fresh,
            revision_topics, revision_day=is_revision_day
        )

        weekly.append({
            "day": day_name,
            "focus": "Revision & mixed practice" if is_revision_day else (
                ", ".join(s["topic"] for s in day_sessions if s["type"] in ("weak", "new")) or "Practice"
            ),
            "total_minutes": sum(s["minutes"] for s in day_sessions),
            "sessions": [
                {"topic": s["topic"], "type": s["type"], "minutes": s["minutes"]}
                for s in day_sessions
            ],
        })

    # ---- allocation summary ----
    by_type: Dict[str, int] = {}
    for s in sessions:
        by_type[s["type"]] = by_type.get(s["type"], 0) + s["minutes"]

    return {
        "preparation_level": preparation_level,
        "total_minutes": total_minutes,
        "sessions": sessions,
        "daily_schedule": sessions,
        "weekly_schedule": weekly,
        "weekly_minutes": sum(d["total_minutes"] for d in weekly),
        "allocation": by_type,
        "plan_date": _date.today().isoformat(),
    }
