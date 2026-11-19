"""Account logic: register, login, and finding the current user."""
import re
import time

from database.models import User, Student
from services.security import hash_password, verify_password, create_access_token

EMAIL_PATTERN = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")

MAX_FAILED_LOGINS = 5
LOCK_WINDOW_SECONDS = 15 * 60

# email -> list of failed-login times. Kept in memory, so it resets when the
# server restarts. This is a simple guard against password guessing.
_failed_logins = {}


class AuthError(Exception):
    def __init__(self, status_code, message):
        super().__init__(message)
        self.status_code = status_code
        self.message = message


def normalize_email(email):
    return (email or "").strip().lower()


def _recent_failures(email, now):
    recent = [t for t in _failed_logins.get(email, []) if now - t < LOCK_WINDOW_SECONDS]
    _failed_logins[email] = recent
    return recent


def reset_login_guard():
    _failed_logins.clear()


def serialize_user(user):
    return {"id": user.id, "email": user.email, "full_name": user.full_name}


def register_user(db, full_name, email, password):
    full_name = (full_name or "").strip()
    email = normalize_email(email)

    if not full_name or len(full_name) > 80:
        raise AuthError(422, "Please enter your name (up to 80 characters).")
    if not EMAIL_PATTERN.match(email) or len(email) > 254:
        raise AuthError(422, "Please enter a valid email address.")
    if len(password or "") < 8:
        raise AuthError(422, "Password must be at least 8 characters.")
    if len(password) > 128:
        raise AuthError(422, "Password is too long (maximum 128 characters).")

    if db.query(User).filter(User.email == email).first():
        raise AuthError(409, "An account with this email already exists.")

    is_first_user = db.query(User).count() == 0

    user = User(email=email, full_name=full_name, password_hash=hash_password(password))
    db.add(user)
    db.flush()

    # Profiles saved before accounts existed have no owner. The very first
    # account takes over the oldest one, so existing work is not lost.
    if is_first_user:
        orphan = (
            db.query(Student)
            .filter(Student.user_id.is_(None))
            .order_by(Student.id)
            .first()
        )
        if orphan:
            orphan.user_id = user.id

    db.commit()
    db.refresh(user)

    return {"token": create_access_token(user.id), "user": serialize_user(user)}


def login_user(db, email, password):
    email = normalize_email(email)
    now = time.time()

    if len(_recent_failures(email, now)) >= MAX_FAILED_LOGINS:
        raise AuthError(429, "Too many failed attempts. Please wait 15 minutes and try again.")

    user = db.query(User).filter(User.email == email).first()

    if user is None or not verify_password(password or "", user.password_hash):
        _failed_logins.setdefault(email, []).append(now)
        # Same message for "no such email" and "wrong password"
        raise AuthError(401, "Incorrect email or password.")

    _failed_logins.pop(email, None)
    return {"token": create_access_token(user.id), "user": serialize_user(user)}
