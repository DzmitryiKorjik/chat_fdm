from __future__ import annotations
from typing import List
from ..schemas import UserPublic
from ..deps import require_admin
from ..schemas import PublicKeyIn, PublicKeyOut
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from ..database import get_db
from ..deps import get_current_user
from ..models import User

router = APIRouter(prefix="/users", tags=["users"])

def _normalize_pubkey(raw: str) -> str:
    """Nettoyage minimal de la clé (trim)."""
    key = (raw or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Clé publique vide")
    if len(key) > 4096:
        raise HTTPException(status_code=400, detail="Clé publique trop longue")
    return key

@router.put("/me/public_key", response_model=PublicKeyOut)
def set_my_public_key(
    payload: PublicKeyIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> PublicKeyOut:
    """🇫🇷 Déclare/remplace la clé publique de l'utilisateur courant."""
    current.public_key = _normalize_pubkey(payload.public_key)
    db.add(current)
    db.commit()
    db.refresh(current)
    return PublicKeyOut(user_id=current.id, username=current.username, public_key=current.public_key)

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

@router.get("/{user_id}/public_key", response_model=PublicKeyOut)
def get_user_public_key(
    user_id: int,
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
) -> PublicKeyOut:
    """🇫🇷 Récupère la clé publique d'un utilisateur (pour chiffrer un message)."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    return PublicKeyOut(user_id=user.id, username=user.username, public_key=user.public_key)

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