from __future__ import annotations
from ..schemas import ConnectionIn, ConnectionOut
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from datetime import datetime, timezone, timedelta
from typing import List
from ..database import get_db
from ..models import Connection, User
from ..deps import get_current_user, require_admin

router = APIRouter(tags=["connections"])

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
        existing.last_seen = last_seen_at
        db.add(existing)
        db.commit()
        db.refresh(existing)
        conn = existing
    else:
        conn = Connection(owner_id=current.id, peer_id=payload.peer_id, transport=payload.transport,
                          address=payload.address, last_seen=last_seen_at)
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return ConnectionOut(peer_id=conn.peer_id, transport=conn.transport, address=conn.address,
                         last_seen=conn.last_seen_at)

@router.get("")
def list_connections(
    minutes: int = Query(10, ge=1, le=1440),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> List[dict]:
    """🇫🇷 Liste des connexions vues récemment (last_seen dans les N minutes)."""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    rows = (
        db.query(Connection)
        .filter(Connection.last_seen >= since)
        .order_by(Connection.last_seen.desc())
        .all()
    )
    return [
        {
            "owner_id": c.owner_id,
            "transport": c.transport,
            "address": c.address,
            "last_seen": c.last_seen,
        }
        for c in rows
    ]
