"""
The one place that reads questions. Since Step 1 they come from the `questions`
table (before: Dataset/questions.csv, which is now only a seed file).

SERVING RULE
    Only questions with status = 'reviewed' are served.
    For LOCAL TESTING ONLY you can also serve drafts by setting the environment
    variable SERVE_DRAFT_QUESTIONS=1. It is OFF by default.

Every function returns plain dicts with the same keys the CSV rows had
(question_id, subject, topic, difficulty, question, option_a..option_d,
correct_answer), so the routers and services did not need to change.
"""
import os
from contextlib import contextmanager

from sqlalchemy import func

from database.connection import SessionLocal
from database.models import Question

# Tests can replace this with a factory bound to a temporary database.
_session_factory = None


def set_session_factory(factory):
    """Used by tests. Pass None to go back to the normal database."""
    global _session_factory
    _session_factory = factory


@contextmanager
def _session(db=None):
    """Use the caller's session if given, otherwise open (and close) our own."""
    if db is not None:
        yield db
        return
    session = (_session_factory or SessionLocal)()
    try:
        yield session
    finally:
        session.close()


def serving_statuses():
    if os.environ.get("SERVE_DRAFT_QUESTIONS", "").strip() == "1":
        return ["reviewed", "draft"]
    return ["reviewed"]


def _served(query):
    return query.filter(Question.status.in_(serving_statuses()))


def to_dict(q):
    return {
        "question_id": q.id,
        "subject": q.subject,
        "topic": q.topic,
        "difficulty": q.difficulty,
        "question": q.question,
        "option_a": q.option_a,
        "option_b": q.option_b,
        "option_c": q.option_c,
        "option_d": q.option_d,
        "correct_answer": q.correct_answer,
        "explanation": q.explanation,
        "diagnostic": "yes" if q.is_diagnostic else "no",
    }


def load_questions(db=None):
    """All served questions, in id order (the same order as the old CSV)."""
    with _session(db) as session:
        rows = _served(session.query(Question)).order_by(Question.id).all()
        return [to_dict(q) for q in rows]


def load_diagnostic_questions(db=None):
    """The short set used for the diagnostic test (is_diagnostic = true).
    The quiz uses ALL served questions."""
    with _session(db) as session:
        rows = (
            _served(session.query(Question))
            .filter(Question.is_diagnostic.is_(True))
            .order_by(Question.id)
            .all()
        )
        return [to_dict(q) for q in rows]


def get_question(question_id, db=None):
    """Returns one served question (with the correct answer), or None.
    A draft question is not found when drafts are not being served."""
    with _session(db) as session:
        q = _served(session.query(Question)).filter(Question.id == question_id).first()
        return to_dict(q) if q else None


def available_topics(answered_question_ids=None, db=None):
    """
    Topics that still have an unanswered served question, in the order their
    first question appears (lowest id first), as a list of topic names.
    Same result as walking the old CSV top to bottom.
    """
    answered = list(answered_question_ids or [])
    with _session(db) as session:
        query = _served(
            session.query(Question.topic, func.min(Question.id))
        )
        if answered:
            query = query.filter(Question.id.notin_(answered))
        rows = (
            query.group_by(Question.topic)
            .order_by(func.min(Question.id))
            .all()
        )
        return [topic for topic, _ in rows]


def next_question(topic, difficulty, answered_question_ids=None, db=None):
    """
    The first unanswered served question of this topic and difficulty (lowest id).
    If there is none at that difficulty, the first unanswered one of the topic.
    Returns a question dict, or None.
    """
    answered = list(answered_question_ids or [])
    with _session(db) as session:
        base = _served(session.query(Question)).filter(Question.topic == topic)
        if answered:
            base = base.filter(Question.id.notin_(answered))

        q = base.filter(Question.difficulty == difficulty).order_by(Question.id).first()
        if q is None:
            q = base.order_by(Question.id).first()
        return to_dict(q) if q else None
