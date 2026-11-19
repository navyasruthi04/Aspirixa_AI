from datetime import datetime, timezone

from sqlalchemy import (
    Column, Integer, String, Float, Text, Date, DateTime, JSON, Boolean,
    ForeignKey, UniqueConstraint, Index
)
from sqlalchemy.orm import relationship

from database.connection import Base


def _now():
    return datetime.now(timezone.utc)


# ----------------------------------------------------------------------
# Accounts (added in Phase 2)
# ----------------------------------------------------------------------
class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)

    email = Column(String, unique=True, index=True, nullable=False)
    password_hash = Column(String, nullable=False)
    full_name = Column(String, nullable=False)

    created_at = Column(DateTime, default=_now, nullable=False)


# ----------------------------------------------------------------------
# Existing model. Only user_id was added so each student profile
# belongs to one account.
# ----------------------------------------------------------------------
class Student(Base):
    __tablename__ = "students"

    id = Column(Integer, primary_key=True, index=True)

    name = Column(String, nullable=False)
    qualification = Column(String, nullable=False)
    age = Column(Integer, nullable=True)

    target_exam = Column(String, nullable=True)
    preparation_level = Column(String, nullable=False)

    study_hours = Column(Float, nullable=False)

    interested_field = Column(String, nullable=True)
    subject_preferences = Column(String, nullable=True)

    learning_preferences = Column(String, nullable=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)


# ----------------------------------------------------------------------
# SSC examinations (added in Phase 2)
# ----------------------------------------------------------------------
class SSCExam(Base):
    """One row per SSC examination (CGL, CHSL, MTS, ...)."""

    __tablename__ = "ssc_exams"

    id = Column(Integer, primary_key=True, index=True)

    code = Column(String, unique=True, index=True, nullable=False)   # e.g. "CGL"
    name = Column(String, nullable=False)                            # e.g. "SSC CGL"
    full_name = Column(String, nullable=True)
    description = Column(Text, nullable=True)

    qualification = Column(Text, nullable=True)
    age_limit = Column(Text, nullable=True)
    age_relaxation = Column(Text, nullable=True)

    # List of tiers: sections, marks, duration, negative marking
    pattern = Column(JSON, nullable=True)

    official_url = Column(String, nullable=True)

    # "available" = details filled in, "pending" = not added yet
    data_status = Column(String, nullable=False, default="pending")

    sources = Column(JSON, nullable=True)       # [{"name": ..., "url": ...}]
    last_verified = Column(Date, nullable=True)

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    notifications = relationship(
        "SSCNotification",
        back_populates="exam",
        cascade="all, delete-orphan",
        order_by="SSCNotification.notification_date.desc()",
    )


class SSCNotification(Base):
    """One row per notification cycle of an exam (e.g. CGL 2026)."""

    __tablename__ = "ssc_notifications"

    __table_args__ = (
        # Stops the same notification from being saved twice
        UniqueConstraint("exam_code", "notification_ref", name="uq_exam_notification"),
    )

    id = Column(Integer, primary_key=True, index=True)

    exam_code = Column(String, ForeignKey("ssc_exams.code"), index=True, nullable=False)
    notification_ref = Column(String, nullable=False)    # e.g. "CGL-2026"
    title = Column(String, nullable=False)

    notification_date = Column(Date, nullable=True)
    apply_start = Column(Date, nullable=True)
    apply_end = Column(Date, nullable=True)
    fee_last_date = Column(Date, nullable=True)
    correction_start = Column(Date, nullable=True)
    correction_end = Column(Date, nullable=True)

    exam_notice_date = Column(Date, nullable=True)       # date of the exam-schedule notice
    tier1_start = Column(Date, nullable=True)
    tier1_end = Column(Date, nullable=True)
    tier2_info = Column(String, nullable=True)

    vacancies = Column(Integer, nullable=True)
    vacancy_note = Column(Text, nullable=True)
    fee_text = Column(String, nullable=True)
    eligibility_note = Column(Text, nullable=True)
    admit_card_info = Column(Text, nullable=True)
    result_info = Column(Text, nullable=True)

    notice_pdf_url = Column(String, nullable=True)
    apply_url = Column(String, nullable=True)

    # Where the data came from
    source_name = Column(String, nullable=True)
    source_url = Column(String, nullable=True)
    sources = Column(JSON, nullable=True)
    # "official" = read from ssc.gov.in, "secondary" = reported by other sites
    verification = Column(String, nullable=False, default="secondary")
    last_verified = Column(Date, nullable=True)
    discrepancies = Column(JSON, nullable=True)          # list of plain-text notes

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)

    exam = relationship("SSCExam", back_populates="notifications")


# ----------------------------------------------------------------------
# Official notice sync (added in Phase 3)
# ----------------------------------------------------------------------
class SSCNotice(Base):
    """One row per notice found on the official SSC notice board."""

    __tablename__ = "ssc_notices"

    id = Column(Integer, primary_key=True, index=True)

    # Stops duplicates: the SSC notice id, or "pdf:<url>" for manual PDFs
    uid = Column(String, unique=True, index=True, nullable=False)

    headline = Column(Text, nullable=False)
    exam_code = Column(String, index=True, nullable=True)   # CGL, CHSL ... or None
    exam_id_raw = Column(String, nullable=True)

    published_on = Column(Date, nullable=True)
    start_date = Column(Date, nullable=True)
    end_date = Column(Date, nullable=True)

    attachment_url = Column(String, nullable=True)
    source_url = Column(String, nullable=True)

    # none | pending | extracted | failed | unavailable
    pdf_status = Column(String, nullable=False, default="none")
    extracted = Column(JSON, nullable=True)      # facts read from the PDF
    extract_note = Column(Text, nullable=True)

    verification = Column(String, nullable=False, default="official")
    first_seen_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class SyncLog(Base):
    """One row per synchronisation run."""

    __tablename__ = "ssc_sync_logs"

    id = Column(Integer, primary_key=True, index=True)

    trigger = Column(String, nullable=False)       # scheduled | manual | manual_pdf
    started_at = Column(DateTime, default=_now, nullable=False)
    finished_at = Column(DateTime, nullable=True)

    # success | partial | failed | blocked
    status = Column(String, nullable=False, default="failed")
    fetched = Column(Integer, nullable=False, default=0)
    new_count = Column(Integer, nullable=False, default=0)
    updated_count = Column(Integer, nullable=False, default=0)
    pdf_count = Column(Integer, nullable=False, default=0)
    message = Column(Text, nullable=True)



# ----------------------------------------------------------------------
# SSC syllabus (Phase 4)
# ----------------------------------------------------------------------
class SyllabusTopic(Base):
    """One row per syllabus topic of an exam tier (e.g. CGL > Tier 1 > Quant > Algebra)."""

    __tablename__ = "syllabus_topics"

    id = Column(Integer, primary_key=True, index=True)

    key = Column(String(180), unique=True, index=True, nullable=False)  # stable id
    exam_code = Column(String(20), index=True, nullable=False)
    tier = Column(String(40), nullable=False)
    subject = Column(String(120), nullable=False)
    area = Column(String(80), nullable=False)
    subject_note = Column(Text, nullable=True)
    topic = Column(String(180), nullable=False)
    subtopics = Column(JSON, nullable=False)
    sort_order = Column(Integer, nullable=False)

    created_at = Column(DateTime, default=_now, nullable=False)
    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class SyllabusProgress(Base):
    """A row exists when a student has marked a topic as completed."""

    __tablename__ = "syllabus_progress"

    __table_args__ = (
        UniqueConstraint("user_id", "topic_id", name="uq_syllabus_user_topic"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    topic_id = Column(Integer, ForeignKey("syllabus_topics.id", ondelete="CASCADE"), index=True, nullable=False)
    completed_at = Column(DateTime, nullable=False)


# ----------------------------------------------------------------------
# Student results (Phase 5): what the student actually did
# ----------------------------------------------------------------------
class DiagnosticResult(Base):
    """One row each time a student submits the diagnostic test."""

    __tablename__ = "diagnostic_results"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    total_answered = Column(Integer, nullable=False)
    correct_answers = Column(Integer, nullable=False)
    score_percentage = Column(Float, nullable=False)

    topic_analysis = Column(JSON, nullable=True)   # [{"topic", "mastery_probability", "status"}]
    weak_topics = Column(JSON, nullable=True)      # ["Percentages", ...]

    created_at = Column(DateTime, default=_now, nullable=False)


class TopicMastery(Base):
    """Latest BKT mastery of each topic for each student (one row per user + topic)."""

    __tablename__ = "topic_mastery"

    __table_args__ = (
        UniqueConstraint("user_id", "topic", name="uq_mastery_user_topic"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    topic = Column(String, nullable=False)
    subject = Column(String, nullable=True)
    mastery = Column(Float, nullable=False)          # 0.0 to 1.0
    status = Column(String, nullable=False)          # Weak | Developing | Mastered
    source = Column(String, nullable=False)          # diagnostic | quiz

    updated_at = Column(DateTime, default=_now, onupdate=_now, nullable=False)


class QuizAttempt(Base):
    """One row for every adaptive-quiz question the student answered."""

    __tablename__ = "quiz_attempts"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    question_id = Column(Integer, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)
    correct = Column(Boolean, nullable=False)

    mastery_before = Column(Float, nullable=False)
    mastery_after = Column(Float, nullable=False)

    created_at = Column(DateTime, default=_now, nullable=False)


# ----------------------------------------------------------------------
# Study plan sessions (Module 3 / Module 5): what the student completed
# ----------------------------------------------------------------------
class StudySession(Base):
    """
    One row per planned session the student has ticked on a given day.
    Completed minutes become the "study time" shown on the dashboard
    and in the performance insights.
    """

    __tablename__ = "study_sessions"

    __table_args__ = (
        UniqueConstraint("user_id", "plan_date", "session_key", name="uq_study_session_day"),
    )

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)

    plan_date = Column(Date, nullable=False, index=True)
    session_key = Column(String, nullable=False)     # e.g. "weak:Percentages"
    topic = Column(String, nullable=True)
    minutes = Column(Integer, nullable=False, default=0)
    completed = Column(Boolean, nullable=False, default=False)
    completed_at = Column(DateTime, nullable=True)


# ----------------------------------------------------------------------
# Question bank (Step 1). The CSV in Dataset/ is now only a seed file.
# ----------------------------------------------------------------------
class Question(Base):
    """
    One multiple-choice question.

    status: 'draft' (written, NOT yet verified by a human) or 'reviewed'
            (a person checked answer, explanation, difficulty and topic).
            Pilot students are only ever served 'reviewed' questions.
    """

    __tablename__ = "questions"
    __table_args__ = (
        Index("ix_questions_subject_topic_difficulty", "subject", "topic", "difficulty"),
    )

    id = Column(Integer, primary_key=True)

    subject = Column(String, nullable=False)
    topic = Column(String, nullable=False)
    difficulty = Column(String, nullable=False)       # Easy / Medium / Hard

    question = Column(Text, nullable=False)
    option_a = Column(Text, nullable=False)
    option_b = Column(Text, nullable=False)
    option_c = Column(Text, nullable=False)
    option_d = Column(Text, nullable=False)
    correct_answer = Column(String(1), nullable=False)  # A / B / C / D
    explanation = Column(Text, nullable=True)

    source = Column(String, nullable=False)            # where the question came from (licence/authorship)
    status = Column(String, nullable=False, default="draft", index=True)
    version = Column(Integer, nullable=False, default=1)
    created_at = Column(DateTime, default=_now, nullable=False)

    # Extra columns needed by the existing diagnostic and by the review tool
    is_diagnostic = Column(Boolean, nullable=False, default=False)
    reviewed_by = Column(String, nullable=True)
    reviewed_at = Column(DateTime, nullable=True)

    tiers = relationship(
        "QuestionTier", cascade="all, delete-orphan", lazy="selectin"
    )


class QuestionTier(Base):
    """Which SSC exam tiers (CGL, CHSL, MTS, CPO, GD, JE) a question suits. Many per question."""

    __tablename__ = "question_tiers"

    question_id = Column(
        Integer, ForeignKey("questions.id", ondelete="CASCADE"), primary_key=True
    )
    tier = Column(String, primary_key=True)
