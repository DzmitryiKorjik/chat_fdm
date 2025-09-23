# Routes utilitaires autour des utilisateurs (annuaire)
from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List
from ..database import get_db
from ..models import User
from ..schemas import UserPublic
from ..deps import get_current_user
from ..deps import require_admin

router = APIRouter(tags=["users"])  # prefix sera ajouté dans main.py si besoin

@router.get("/users", response_model=List[UserPublic])
def list_users(
    q: str | None = Query(None, description="Filtre par fragment de nom"),
    limit: int = 20,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[UserPublic]:
    """ Liste les utilisateurs (exclut l'utilisateur courant)."""
    query = db.query(User).filter(User.id != current.id)
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    rows = query.order_by(User.username.asc()).limit(max(1, min(limit, 100))).all()
    return [UserPublic.model_validate(u) for u in rows]

# ─────────────────────────── Admin only ───────────────────────────

@router.get("/admin/users", response_model=List[UserPublic])
def admin_list_all_users(db: Session = Depends(get_db),
                         admin: User = Depends(require_admin)) -> List[UserPublic]:
    """ Liste complète des utilisateurs (vue admin)."""
    rows = db.query(User).order_by(User.id.asc()).all()
    return [UserPublic.model_validate(u) for u in rows]

@router.post("/admin/users/{user_id}/promote", response_model=UserPublic)
def admin_promote(user_id: int,
                  db: Session = Depends(get_db),
                  admin: User = Depends(require_admin)) -> UserPublic:
    """ Donner les droits admin à un utilisateur."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = True
    db.commit(); db.refresh(user)
    return UserPublic.model_validate(user)

@router.post("/admin/users/{user_id}/demote", response_model=UserPublic)
def admin_demote(user_id: int,
                 db: Session = Depends(get_db),
                 admin: User = Depends(require_admin)) -> UserPublic:
    """ Retirer les droits admin d'un utilisateur."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se rétrograder soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = False
    db.commit(); db.refresh(user)
    return UserPublic.model_validate(user)

@router.delete("/admin/users/{user_id}", status_code=204)
def admin_delete_user(user_id: int,
                      db: Session = Depends(get_db),
                      admin: User = Depends(require_admin)) -> None:
    """ Supprimer un utilisateur (irréversible)."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se supprimer soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user); db.commit()