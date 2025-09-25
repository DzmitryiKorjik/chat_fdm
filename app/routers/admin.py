from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import require_admin
from ..models import User
from ..schemas import UserPublic

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/users", response_model=List[UserPublic])
def admin_list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> List[UserPublic]:
    rows = db.query(User).order_by(User.id.asc()).all()
    return [UserPublic.model_validate(u) for u in rows]


@router.post("/users/{user_id:int}/promote", response_model=UserPublic)
def admin_promote(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> UserPublic:
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.post("/users/{user_id:int}/demote", response_model=UserPublic)
def admin_demote(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> UserPublic:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se rétrograder soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = False
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.delete("/users/{user_id:int}", status_code=204)
def admin_delete_user(
    user_id: int, db: Session = Depends(get_db), admin: User = Depends(require_admin)
) -> None:
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se supprimer soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
