"""Dépendances FastAPI (injection) : session DB et utilisateur courant."""

from __future__ import annotations

import logging
from typing import Optional

# Dépendance: exige un admin
from fastapi import Depends, Header, HTTPException, Request, status
from sqlalchemy.orm import Session

from .auth import decode_access_token
from .connections_util import upsert_connection
from .database import get_db
from .models import User

logger = logging.getLogger(__name__)


def get_user_by_username(db: Session, username: str) -> Optional[User]:
    """Récupère un utilisateur par son nom (helper partagé)."""
    return db.query(User).filter(User.username == username).first()


def get_current_user(
    request: Request,
    db: Session = Depends(get_db),
    authorization: Optional[str] = Header(None, alias="Authorization"),
) -> User:
    """Extrait le JWT de l'en-tête Authorization et retourne l'utilisateur courant.
    Format attendu : "Authorization: Bearer <token>"
    """
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Authorization manquante"
        )
    token = authorization.split(" ", 1)[1]
    username = decode_access_token(token)
    user = get_user_by_username(db, username)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Utilisateur introuvable"
        )

    # Marquer l'activité HTTP (adresse IP du client)
    try:
        client_ip = request.client.host if request and request.client else "unknown"
        upsert_connection(db, user.id, transport="http", address=client_ip)
    except Exception as exc:
        # on n'empêche pas la requête en cas d'erreur de télémétrie, mais on loggue
        logger.warning("Échec upsert_connection (télémétrie): %s", exc, exc_info=True)

    return user


def require_admin(current: User = Depends(get_current_user)) -> User:
    """Autorise uniquement les administrateurs."""
    if not current.is_admin:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Admin only")
    return current
