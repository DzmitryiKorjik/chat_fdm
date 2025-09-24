from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import User
from ..schemas import PublicKeyIn, PublicKeyOut, UserPublic

# 🇫🇷 NOTE IMPORTANTE :
# Ce routeur a déjà un préfixe "/users".
# NE rajoute PAS encore un prefix="/users" dans main.py pour éviter "/users/users".
router = APIRouter(prefix="/users", tags=["users"])


def _normalize_pubkey(raw: str) -> str:
    """🇫🇷 Nettoyage minimal de la clé publique (trim + borne de taille)."""
    key = (raw or "").strip()
    if not key:
        raise HTTPException(status_code=400, detail="Clé publique vide")
    if len(key) > 4096:
        raise HTTPException(status_code=400, detail="Clé publique trop longue")
    return key


# ─────────────────────────── Clé publique (utilisateur courant) ───────────────────────────


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
    return PublicKeyOut(
        user_id=current.id, username=current.username, public_key=current.public_key
    )


@router.get("/me/public_key", response_model=PublicKeyOut)
def get_my_public_key(
    current: User = Depends(get_current_user),
) -> PublicKeyOut:
    """🇫🇷 Retourne la clé publique de l'utilisateur courant (si définie)."""
    return PublicKeyOut(
        user_id=current.id, username=current.username, public_key=current.public_key
    )


# ⚠️ IMPORTANT : placer la route "me" AVANT la route dynamique pour éviter
# que "me" soit interprété comme {user_id}. On borne aussi user_id à int.


@router.get("/{user_id:int}/public_key", response_model=PublicKeyOut)
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


# ─────────────────────────── Liste des utilisateurs ───────────────────────────


@router.get("", response_model=List[UserPublic])
def list_users(
    q: str | None = Query(None, description="🇫🇷 Filtre par fragment de nom"),
    limit: int = 20,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[UserPublic]:
    """🇫🇷 Liste des utilisateurs (exclut l'utilisateur courant)."""
    query = db.query(User).filter(User.id != current.id)
    if q:
        query = query.filter(User.username.ilike(f"%{q}%"))
    rows = query.order_by(User.username.asc()).limit(max(1, min(limit, 100))).all()
    return [UserPublic.model_validate(u) for u in rows]


# ─────────────────────────── Admin only ───────────────────────────
# ⚠️ Ces routes seront accessibles via /users/admin/...
# Si tu veux /admin/users sans le /users devant, mets ces routes
# dans un autre routeur avec prefix="/admin" et include_router(...) séparément.


@router.get("/admin/users", response_model=List[UserPublic])
def admin_list_all_users(
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> List[UserPublic]:
    """🇫🇷 Liste complète des utilisateurs (vue admin)."""
    rows = db.query(User).order_by(User.id.asc()).all()
    return [UserPublic.model_validate(u) for u in rows]


@router.post("/admin/users/{user_id:int}/promote", response_model=UserPublic)
def admin_promote(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserPublic:
    """🇫🇷 Donner les droits admin à un utilisateur."""
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = True
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.post("/admin/users/{user_id:int}/demote", response_model=UserPublic)
def admin_demote(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> UserPublic:
    """🇫🇷 Retirer les droits admin d'un utilisateur."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se rétrograder soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    user.is_admin = False
    db.commit()
    db.refresh(user)
    return UserPublic.model_validate(user)


@router.delete("/admin/users/{user_id:int}", status_code=204)
def admin_delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> None:
    """🇫🇷 Supprimer un utilisateur (irréversible)."""
    if user_id == admin.id:
        raise HTTPException(status_code=400, detail="Impossible de se supprimer soi-même")
    user = db.get(User, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur introuvable")
    db.delete(user)
    db.commit()
