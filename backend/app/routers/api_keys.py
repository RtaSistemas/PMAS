"""Service keys for automatic timesheet import (administrator only).

A key acts as an existing user, so the role and the PEP ACL of that user apply.
The server shows the key once, when it creates it, and keeps only a hash.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user, hash_api_key, new_api_key
from backend.app.limiter import limiter
from backend.app.models import ApiKey, User
from backend.app.schemas import ApiKeyCreatedOut, ApiKeyCreateIn, ApiKeyOut
from backend.app.utils import now_br

router = APIRouter(
    prefix="/api/api-keys",
    tags=["api-keys"],
    dependencies=[Depends(get_current_user)],
)


def _out(key: ApiKey) -> dict:
    return {
        "id": key.id, "name": key.name, "key_prefix": key.key_prefix,
        "username": key.user.username, "created_by": key.created_by,
        "created_at": key.created_at, "last_used_at": key.last_used_at,
        "revoked_at": key.revoked_at,
    }


@router.get("", summary="Listar chaves de API", response_model=list[ApiKeyOut])
def list_keys(db: DbSession, _admin: AdminUser):
    return [_out(k) for k in db.query(ApiKey).order_by(ApiKey.created_at.desc()).all()]


@router.post("", summary="Criar chave de API", status_code=201, response_model=ApiKeyCreatedOut)
@limiter.limit("30/minute")
def create_key(request: Request, body: ApiKeyCreateIn, db: DbSession, admin: AdminUser):
    user = db.get(User, body.user_id) if body.user_id else admin
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if user.must_change_password:
        raise HTTPException(
            status_code=400,
            detail="O usuário deve alterar a senha antes de receber uma chave.",
        )
    raw = new_api_key()
    key = ApiKey(
        name=body.name.strip(), key_prefix=raw[:10], key_hash=hash_api_key(raw),
        user_id=user.id, created_by=admin.username,
    )
    db.add(key)
    db.flush()
    log_audit(db, admin, "create", "api_key", key.id, {"name": key.name, "acts_as": user.username})
    db.commit()
    db.refresh(key)
    return {**_out(key), "key": raw}


@router.delete("/{key_id}", summary="Revogar chave de API", response_model=ApiKeyOut)
def revoke_key(key_id: int, db: DbSession, admin: AdminUser):
    key = db.get(ApiKey, key_id)
    if key is None:
        raise HTTPException(status_code=404, detail="Chave não encontrada.")
    if key.revoked_at is None:
        key.revoked_at = now_br()
        log_audit(db, admin, "revoke", "api_key", key.id, {"name": key.name})
        db.commit()
        db.refresh(key)
    return _out(key)
