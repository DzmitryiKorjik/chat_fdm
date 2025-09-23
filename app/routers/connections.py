from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from datetime import datetime, timezone
from ..schemas import ConnectionIn, ConnectionOut
from ..models import Connection, User
from ..database import get_db
from ..deps import get_current_user

router = APIRouter(prefix="/connections", tags=["connections"])

@router.post("/upsert", response_model=ConnectionOut)
def upsert_connection(
    payload: ConnectionIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ConnectionOut:
    """ Crée ou met à jour une entrée de voisin pour l'utilisateur courant."""
    existing = (
        db.query(Connection)
        .filter(Connection.owner_id == current.id, Connection.peer_id == payload.peer_id)
        .first()
    )
    last_seen_at = (
        datetime.fromtimestamp(payload.last_seen_ms / 1000, tz=timezone.utc)
        if payload.last_seen_ms is not None
        else datetime.now(timezone.utc)
    )
    if existing:
        existing.transport = payload.transport
        existing.address = payload.address
        existing.last_seen_at = last_seen_at
        db.add(existing)
        db.commit()
        db.refresh(existing)
        conn = existing
    else:
        conn = Connection(owner_id=current.id, peer_id=payload.peer_id, transport=payload.transport,
                          address=payload.address, last_seen_at=last_seen_at)
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return ConnectionOut(peer_id=conn.peer_id, transport=conn.transport, address=conn.address,
                         last_seen_at=conn.last_seen_at)

@router.get("", response_model=List[ConnectionOut])
def list_connections(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[ConnectionOut]:
    """ Liste les voisins connus de l'utilisateur courant, ordonnés par dernière vue."""
    rows = (
        db.query(Connection)
        .filter(Connection.owner_id == current.id)
        .order_by(Connection.last_seen_at.desc())
        .all()
    )
    return [ConnectionOut(peer_id=r.peer_id, transport=r.transport, address=r.address, last_seen_at=r.last_seen_at) for
            r in rows]
