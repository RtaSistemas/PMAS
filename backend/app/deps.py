from __future__ import annotations

import logging
import os
import hashlib
import secrets
from typing import Annotated

from fastapi import Depends, Header, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt

from backend.app.database import DbSession
from backend.app.models import ApiKey, User
from backend.app.utils import now_br

log = logging.getLogger(__name__)

# PMAS_ENV=production needs a fixed signing key. Without one, every restart would log out all
# users. Any other value of PMAS_ENV (or none) is development, the same rule as run.py.
_MIN_KEY_LENGTH = 32
_IS_PRODUCTION = os.getenv("PMAS_ENV", "development").strip().lower() == "production"
_env_secret = os.getenv("PMAS_SECRET_KEY")
if _IS_PRODUCTION:
    if not _env_secret or len(_env_secret.strip()) < _MIN_KEY_LENGTH:
        raise RuntimeError(
            "PMAS_ENV=production needs the PMAS_SECRET_KEY variable with at least "
            f"{_MIN_KEY_LENGTH} characters. Set it in the settings file "
            "(see docs/OPERATIONS.md) and start PMAS again."
        )
    SECRET_KEY = _env_secret
elif _env_secret:
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


def _resolve_user(token: str, db) -> User:
    """Decode the JWT and return the User row; raises 401 on any failure."""
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


def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    user = _resolve_user(token, db)
    if getattr(user, "must_change_password", False):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Senha temporária — altere a senha antes de continuar.",
            headers={"X-PMAS-Must-Change-Password": "true"},
        )
    return user


def get_current_user_allow_change(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: DbSession,
) -> User:
    """Same as get_current_user but does not block users with must_change_password.
    Used exclusively by the change-password endpoint so that a forced-change user
    can authenticate long enough to set a new password.
    """
    return _resolve_user(token, db)


API_KEY_PREFIX = "pmas_"


def hash_api_key(raw: str) -> str:
    """Keys are long random strings, so a fast hash is enough. The raw key is never stored."""
    return hashlib.sha256(raw.encode()).hexdigest()


def new_api_key() -> str:
    return API_KEY_PREFIX + secrets.token_urlsafe(32)


oauth2_optional = OAuth2PasswordBearer(tokenUrl="/api/token", auto_error=False)


def get_upload_user(
    request: Request,
    db: DbSession,
    token: Annotated[str | None, Depends(oauth2_optional)] = None,
    api_key: Annotated[str | None, Header(alias="X-API-Key")] = None,
) -> User:
    """User for POST /api/upload-timesheet: an API key or a normal login token.
    Only the upload endpoint uses this dependency, so a key cannot reach any other route."""
    if api_key:
        record = (
            db.query(ApiKey)
            .filter(ApiKey.key_hash == hash_api_key(api_key), ApiKey.revoked_at.is_(None))
            .first()
        )
        if record is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Chave de API inválida ou revogada.",
            )
        if getattr(record.user, "must_change_password", False):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="O usuário desta chave deve alterar a senha antes de continuar.",
            )
        record.last_used_at = now_br()
        db.commit()
        request.state.api_key = record
        return record.user
    if not token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Not authenticated",
            headers={"WWW-Authenticate": "Bearer"},
        )
    return get_current_user(token, db)


CurrentUser = Annotated[User, Depends(get_current_user)]
UploadUser = Annotated[User, Depends(get_upload_user)]
CurrentUserFlex = Annotated[User, Depends(get_current_user_allow_change)]


def require_admin(current_user: CurrentUser) -> User:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Acesso restrito a administradores.",
        )
    return current_user


AdminUser = Annotated[User, Depends(require_admin)]
