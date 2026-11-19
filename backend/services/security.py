"""
Password hashing and login tokens for Aspirixa.

Only Python's standard library is used, so there is nothing new to install.

- Passwords are never stored. We store a salted PBKDF2-SHA256 hash.
- Login tokens are standard JWT (HS256), signed with a secret key.
- The secret key comes from the ASPIRIXA_SECRET_KEY environment variable.
  If it is not set, a random key is created once and saved in
  database/.secret_key so that logins survive a server restart.
"""
import base64
import hashlib
import hmac
import json
import os
import secrets
import time
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parents[2]
SECRET_KEY_FILE = BASE_DIR / "database" / ".secret_key"

PBKDF2_ITERATIONS = 600_000
TOKEN_LIFETIME_SECONDS = 7 * 24 * 60 * 60  # 7 days


# ------------------------------------------------------------------
# Secret key
# ------------------------------------------------------------------
def get_secret_key() -> bytes:
    from_env = os.environ.get("ASPIRIXA_SECRET_KEY")
    if from_env:
        return from_env.encode("utf-8")

    if SECRET_KEY_FILE.exists():
        return SECRET_KEY_FILE.read_text(encoding="utf-8").strip().encode("utf-8")

    key = secrets.token_hex(32)
    SECRET_KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
    SECRET_KEY_FILE.write_text(key, encoding="utf-8")
    return key.encode("utf-8")


# ------------------------------------------------------------------
# Passwords
# ------------------------------------------------------------------
def hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS
    )
    return "pbkdf2_sha256${}${}${}".format(
        PBKDF2_ITERATIONS,
        base64.b64encode(salt).decode("ascii"),
        base64.b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, stored_hash: str) -> bool:
    try:
        scheme, iterations, salt_b64, digest_b64 = stored_hash.split("$")
        if scheme != "pbkdf2_sha256":
            return False
        salt = base64.b64decode(salt_b64)
        expected = base64.b64decode(digest_b64)
        actual = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, int(iterations)
        )
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


# ------------------------------------------------------------------
# JWT (HS256)
# ------------------------------------------------------------------
def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _b64url_decode(text: str) -> bytes:
    padding = "=" * (-len(text) % 4)
    return base64.urlsafe_b64decode(text + padding)


def _sign(signing_input: str) -> str:
    signature = hmac.new(
        get_secret_key(), signing_input.encode("ascii"), hashlib.sha256
    ).digest()
    return _b64url_encode(signature)


def create_access_token(user_id: int, lifetime_seconds: int = TOKEN_LIFETIME_SECONDS) -> str:
    now = int(time.time())
    header = {"alg": "HS256", "typ": "JWT"}
    payload = {"sub": str(user_id), "iat": now, "exp": now + lifetime_seconds}

    signing_input = "{}.{}".format(
        _b64url_encode(json.dumps(header, separators=(",", ":")).encode("utf-8")),
        _b64url_encode(json.dumps(payload, separators=(",", ":")).encode("utf-8")),
    )
    return "{}.{}".format(signing_input, _sign(signing_input))


def decode_access_token(token: str):
    """Returns the user id if the token is valid and not expired, else None."""
    try:
        header_b64, payload_b64, signature = token.split(".")
        signing_input = "{}.{}".format(header_b64, payload_b64)

        if not hmac.compare_digest(_sign(signing_input), signature):
            return None

        header = json.loads(_b64url_decode(header_b64))
        if header.get("alg") != "HS256":
            return None

        payload = json.loads(_b64url_decode(payload_b64))
        if int(payload["exp"]) < int(time.time()):
            return None

        return int(payload["sub"])
    except (ValueError, KeyError, TypeError):
        return None
