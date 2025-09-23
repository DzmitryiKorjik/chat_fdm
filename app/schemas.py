from __future__ import annotations
from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, List

class UserCreate(BaseModel):
    """ Données requises pour créer / authentifier un utilisateur."""
    username: str = Field(..., min_length=3, max_length=64)
    password: str = Field(..., min_length=6)

class TokenResponse(BaseModel):
    """ Réponse renvoyant un token JWT et sa durée de vie (secondes/minutes)."""
    access_token: str
    token_type: str = "bearer"
    expires_in: int

class MessageIn(BaseModel):
    """ Corps d'un message à créer."""
    content: str = Field(..., min_length=1, max_length=10_000)

class MessageOut(BaseModel):
    """ Représentation publique d'un message."""
    id: int
    room_id: str
    sender: str
    content: str
    created_at: datetime

class ConnectionIn(BaseModel):
    """ Déclaration/MAJ d'un voisin (peer)."""
    peer_id: str
    transport: str
    address: str
    last_seen_ms: Optional[int] = None

class ConnectionOut(BaseModel):
    """ Représentation d'un voisin connu."""
    peer_id: str
    transport: str
    address: str
    last_seen_at: datetime

# Exposition publique d'un utilisateur (sans champs sensibles)
class UserPublic(BaseModel):
    id: int
    username: str
    is_admin: bool

    class Config:
        from_attributes = True

# Requête pour ouvrir une DM
class OpenDMRequest(BaseModel):
    # on ouvre une DM par ID de destinataire
    peer_id: int

# Réponse contenant le room_id de la DM
class OpenDMResponse(BaseModel):
    room_id: str