from __future__ import annotations
from datetime import datetime, timezone
from sqlalchemy.orm import Session
from .models import Connection

def upsert_connection(db: Session, user_id: int, transport: str, address: str) -> None:
    """🇫🇷 Crée/MAJ une connexion pour (user, transport, adresse)."""
    row = (
        db.query(Connection)
        .filter(Connection.owner_id == user_id,
                Connection.transport == transport,
                Connection.address == address)
        .first()
    )
    now = datetime.now(timezone.utc)
    if row:
        row.last_seen = now
    else:
        db.add(Connection(owner_id=user_id, transport=transport, address=address, last_seen=now))
    db.commit()
