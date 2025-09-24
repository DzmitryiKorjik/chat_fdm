from __future__ import annotations

from datetime import datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, constr


class UserCreate(BaseModel):
    """Données requises pour créer / authentifier un utilisateur."""

    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)
    public_key: Optional[str] = None


class PublicKeyIn(BaseModel):
    """Clé publique fournie par le frontend (PEM/base64)."""

    public_key: constr(min_length=40, max_length=4096)


class PublicKeyOut(BaseModel):
    user_id: int
    username: str
    public_key: Optional[str] = None


class TokenResponse(BaseModel):
    """Réponse renvoyant un token JWT et sa durée de vie (minutes)."""

    access_token: str
    token_type: str = "bearer"
    expires_in: int


class MessageIn(BaseModel):
    """Corps d'un message à créer."""

    content: str = Field(..., min_length=1, max_length=10_000)


class MessageOut(BaseModel):
    """Représentation publique d'un message."""

    id: int
    room_id: str
    sender: str
    content: str
    created_at: datetime


class ConnectionIn(BaseModel):
    """Déclaration/MAJ d'un voisin (peer)."""

    peer_id: str
    transport: str
    address: str
    last_seen_ms: Optional[int] = None


class ConnectionOut(BaseModel):
    """Représentation d'un voisin connu."""

    peer_id: str
    transport: str
    address: str
    last_seen: datetime
    # Si tu veux ajouter l'heure de Paris :
    # last_seen_paris: Optional[str] = None


class UserPublic(BaseModel):
    """Exposition publique d'un utilisateur (sans champs sensibles)."""

    id: int
    username: str
    is_admin: bool

    # Pydantic v2 : équivalent à orm_mode=True
    model_config = ConfigDict(from_attributes=True)


class OpenDMRequest(BaseModel):
    """Requête pour ouvrir une DM (par ID du destinataire)."""

    peer_id: int


class OpenDMResponse(BaseModel):
    """Réponse contenant le room_id de la DM."""

    room_id: str
