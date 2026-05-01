from __future__ import annotations

import logging
import os
import secrets
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.app.database import DbSession
from backend.app.models import User

log = logging.getLogger(__name__)

_env_secret = os.getenv("PMAS_SECRET_KEY")
if _env_secret:
    SECRET_KEY = _env_secret
else:
    SECRET_KEY = secrets.token_hex(32)
    log.warning(
        "PMAS_SECRET_KEY não definida — usando chave aleatória. "
        "Sessões serão invalidadas ao reiniciar o servidor. "
        "Defina PMAS_SECRET_KEY para persistência de sessão."
    )

ALGORITHM = "HS256"

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/token")


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    exc = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Token inválido ou expirado.",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        username: str | None = payload.get("sub")
        if username is None:
            raise exc
    except JWTError:
        raise exc
    user = db.query(User).filter(User.username == username).first()
    if user is None:
        raise exc
    return user


CurrentUser = Annotated[User, Depends(get_current_user)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
