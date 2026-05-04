from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.audit import log_audit
from backend.app.database import DbSession
from backend.app.deps import AdminUser, get_current_user
from backend.app.models import Project, User, UserProjectAccess
from backend.app.schemas import UserProjectAccessIn, UserProjectAccessOut

router = APIRouter(
    prefix="/api/projects",
    tags=["acl"],
    dependencies=[Depends(get_current_user)],
)


def _access_out(entry: UserProjectAccess, pep_wbs: str) -> dict:
    return {
        "id": entry.id,
        "user_id": entry.user_id,
        "username": entry.user.username,
        "project_id": entry.project_id,
        "pep_wbs": pep_wbs,
    }


@router.get("/{project_id}/access", response_model=list[UserProjectAccessOut])
def list_access(project_id: int, db: DbSession):
    """List all users with explicit ACL access to a project."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    entries = (
        db.query(UserProjectAccess)
        .filter(UserProjectAccess.project_id == project_id)
        .all()
    )
    return [_access_out(e, project.pep_wbs) for e in entries]


@router.post("/{project_id}/access", status_code=201, response_model=UserProjectAccessOut)
def grant_access(
    project_id: int,
    body: UserProjectAccessIn,
    db: DbSession,
    current_user: AdminUser,
):
    """Grant upload permission on a project to a user (admin only)."""
    project = db.get(Project, project_id)
    if project is None:
        raise HTTPException(status_code=404, detail="Projeto não encontrado.")
    user = db.get(User, body.user_id)
    if user is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")

    existing = (
        db.query(UserProjectAccess)
        .filter(
            UserProjectAccess.project_id == project_id,
            UserProjectAccess.user_id == body.user_id,
        )
        .first()
    )
    if existing:
        raise HTTPException(status_code=409, detail="Acesso já concedido para este usuário.")

    entry = UserProjectAccess(user_id=body.user_id, project_id=project_id)
    db.add(entry)
    db.flush()
    log_audit(
        db, current_user, "grant_access", "project", project_id,
        {"user_id": body.user_id, "username": user.username, "pep_wbs": project.pep_wbs},
    )
    db.commit()
    db.refresh(entry)
    return _access_out(entry, project.pep_wbs)


@router.delete("/{project_id}/access/{user_id}", status_code=204)
def revoke_access(
    project_id: int,
    user_id: int,
    db: DbSession,
    current_user: AdminUser,
):
    """Revoke upload permission for a user on a project (admin only)."""
    entry = (
        db.query(UserProjectAccess)
        .filter(
            UserProjectAccess.project_id == project_id,
            UserProjectAccess.user_id == user_id,
        )
        .first()
    )
    if entry is None:
        raise HTTPException(status_code=404, detail="Acesso não encontrado.")
    log_audit(
        db, current_user, "revoke_access", "project", project_id,
        {"user_id": user_id},
    )
    db.delete(entry)
    db.commit()
