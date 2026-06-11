from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from backend.app.database import DbSession
from backend.app.deps import ALGORITHM, SECRET_KEY
from backend.app.limiter import limiter
from backend.app.models import User
from backend.app.schemas import Token

router = APIRouter(prefix="/api", tags=["auth"])

_TOKEN_EXPIRE_HOURS = 8


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


_MAX_ATTEMPTS = 5
_LOCKOUT_MINUTES = 15


@router.post("/token", response_model=Token)
@limiter.limit("30/minute")
def login(
    request: Request,
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    user = db.query(User).filter(User.username == form.username).first()

    if user:
        locked_until = getattr(user, "locked_until", None)
        if locked_until is not None:
            now_naive = datetime.now(timezone.utc).replace(tzinfo=None)
            if locked_until > now_naive:
                remaining = int((locked_until - now_naive).total_seconds() / 60) + 1
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail=f"Conta bloqueada temporariamente. Tente novamente em {remaining} minuto(s).",
                    headers={"WWW-Authenticate": "Bearer"},
                )

    if not user or not verify_password(form.password, user.hashed_password):
        if user:
            attempts = getattr(user, "failed_login_attempts", 0) + 1
            user.failed_login_attempts = attempts
            if attempts >= _MAX_ATTEMPTS:
                unlock_at = datetime.now(timezone.utc) + timedelta(minutes=_LOCKOUT_MINUTES)
                user.locked_until = unlock_at.replace(tzinfo=None)
            db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Successful login — reset lockout counters
    user.failed_login_attempts = 0
    user.locked_until = None

    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    payload: dict = {"sub": user.username, "role": user.role, "exp": expire}
    if getattr(user, "must_change_password", False):
        payload["must_change"] = True
    token = jwt.encode(payload, SECRET_KEY, algorithm=ALGORITHM)
    db.commit()
    return Token(access_token=token)
