from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database.connection import get_db
from database.models import User
from services.auth_service import (
    AuthError, register_user, login_user, serialize_user
)
from services.security import decode_access_token


router = APIRouter(
    prefix="/auth",
    tags=["Authentication"]
)

bearer_scheme = HTTPBearer(auto_error=False)


class RegisterRequest(BaseModel):
    full_name: str
    email: str
    password: str


class LoginRequest(BaseModel):
    email: str
    password: str


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db)
) -> User:
    """Use as a dependency on any endpoint that needs a logged-in student."""

    unauthorized = HTTPException(
        status_code=401,
        detail="Please sign in to continue.",
        headers={"WWW-Authenticate": "Bearer"}
    )

    if credentials is None:
        raise unauthorized

    user_id = decode_access_token(credentials.credentials)

    if user_id is None:
        raise unauthorized

    user = db.get(User, user_id)

    if user is None:
        raise unauthorized

    return user


@router.post("/register", status_code=201)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    try:
        return register_user(
            db, request.full_name, request.email, request.password
        )
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)


@router.post("/login")
def login(request: LoginRequest, db: Session = Depends(get_db)):
    try:
        return login_user(db, request.email, request.password)
    except AuthError as error:
        raise HTTPException(status_code=error.status_code, detail=error.message)


@router.get("/me")
def me(user: User = Depends(get_current_user)):
    return serialize_user(user)
