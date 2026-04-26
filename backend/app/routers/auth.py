from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Annotated

import bcrypt as _bcrypt
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordRequestForm
from jose import jwt

from backend.app.database import DbSession
from backend.app.deps import ALGORITHM, SECRET_KEY
from backend.app.models import User
from backend.app.schemas import Token

router = APIRouter(prefix="/api", tags=["auth"])

_TOKEN_EXPIRE_HOURS = 8


def hash_password(password: str) -> str:
    return _bcrypt.hashpw(password.encode(), _bcrypt.gensalt()).decode()


def verify_password(plain: str, hashed: str) -> bool:
    return _bcrypt.checkpw(plain.encode(), hashed.encode())


@router.post("/token", response_model=Token)
def login(
    form: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: DbSession,
):
    user = db.query(User).filter(User.username == form.username).first()
    if not user or not verify_password(form.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais inválidas.",
            headers={"WWW-Authenticate": "Bearer"},
        )
    expire = datetime.now(timezone.utc) + timedelta(hours=_TOKEN_EXPIRE_HOURS)
    token = jwt.encode(
        {"sub": user.username, "role": user.role, "exp": expire},
        SECRET_KEY,
        algorithm=ALGORITHM,
    )
    return Token(access_token=token)
