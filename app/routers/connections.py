from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import List

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user, require_admin
from ..models import Connection, User
from ..schemas import ConnectionIn, ConnectionOut

router = APIRouter(tags=["connections"])

# ——— Zone Paris optionnelle ———
try:
    from zoneinfo import ZoneInfo

    TZ_PARIS = ZoneInfo("Europe/Paris")
except Exception:
    TZ_PARIS = None


@router.post("/upsert", response_model=ConnectionOut)
def upsert_connection(
    payload: ConnectionIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> ConnectionOut:
    """Crée ou met à jour une entrée de voisin pour l'utilisateur courant."""
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
        conn = Connection(
            owner_id=current.id,
            peer_id=payload.peer_id,
            transport=payload.transport,
            address=payload.address,
            last_seen=last_seen_at,
        )
        db.add(conn)
        db.commit()
        db.refresh(conn)
    return ConnectionOut(
        peer_id=conn.peer_id,
        transport=conn.transport,
        address=conn.address,
        last_seen=conn.last_seen,
        last_seen_paris=(
            conn.last_seen.astimezone(TZ_PARIS).isoformat()
            if (TZ_PARIS and conn.last_seen)
            else None
        ),
    )


@router.get("")
def list_connections(
    minutes: int = Query(10, ge=1, le=1440),
    db: Session = Depends(get_db),
    admin: User = Depends(require_admin),
) -> List[dict]:
    """🇫🇷 Liste des connexions vues récemment (last_seen UTC + Paris)."""
    since = datetime.now(timezone.utc) - timedelta(minutes=minutes)
    rows = (
        db.query(Connection)
        .filter(Connection.last_seen >= since)
        .order_by(Connection.last_seen.desc())
        .all()
    )
    out = []
    for c in rows:
        ls_paris = (
            c.last_seen.astimezone(TZ_PARIS).isoformat() if (TZ_PARIS and c.last_seen) else None
        )
        out.append(
            {
                "owner_id": c.owner_id,
                "transport": c.transport,
                "address": c.address,
                "last_seen": c.last_seen.isoformat() if c.last_seen else None,  # UTC
                "last_seen_paris": ls_paris,  # Paris
            }
        )
    return out
