from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from backend.app.database import DbSession
from backend.app.deps import AdminUser, CurrentUser, get_current_user
from backend.app.models import User
from backend.app.routers.auth import hash_password, verify_password
from backend.app.schemas import PasswordChangeIn, UserCreateIn, UserOut

router = APIRouter(
    prefix="/api/users",
    tags=["users"],
    dependencies=[Depends(get_current_user)],
)


@router.get("", summary="Listar usuários", response_model=list[UserOut])
def list_users(db: DbSession, _admin: AdminUser):
    return db.query(User).order_by(User.username).all()


@router.post("", summary="Criar usuário", status_code=201, response_model=UserOut)
def create_user(body: UserCreateIn, db: DbSession, _admin: AdminUser):
    if db.query(User).filter(User.username == body.username).first():
        raise HTTPException(status_code=400, detail="Nome de usuário já existe.")
    user = User(
        username=body.username,
        hashed_password=hash_password(body.password),
        role=body.role,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


@router.patch("/{user_id}/password", summary="Alterar senha", response_model=UserOut)
def change_password(
    user_id: int,
    body: PasswordChangeIn,
    db: DbSession,
    current_user: CurrentUser,
):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if current_user.role != "admin" and current_user.id != user_id:
        raise HTTPException(status_code=403, detail="Sem permissão para alterar senha de outro usuário.")
    if current_user.role != "admin":
        if not body.current_password:
            raise HTTPException(status_code=422, detail="Senha atual obrigatória.")
        if not verify_password(body.current_password, target.hashed_password):
            raise HTTPException(status_code=400, detail="Senha atual incorreta.")
    target.hashed_password = hash_password(body.new_password)
    db.commit()
    db.refresh(target)
    return target


@router.delete("/{user_id}", summary="Excluir usuário", status_code=204)
def delete_user(user_id: int, db: DbSession, admin: AdminUser):
    target = db.get(User, user_id)
    if target is None:
        raise HTTPException(status_code=404, detail="Usuário não encontrado.")
    if target.id == admin.id:
        raise HTTPException(status_code=409, detail="Não é possível excluir o próprio usuário.")
    db.delete(target)
    db.commit()
