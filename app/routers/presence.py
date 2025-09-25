from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import Connection, User

router = APIRouter(tags=["presence"])

# ——— zone Paris ———
try:
    from zoneinfo import ZoneInfo  # stdlib

    TZ_PARIS = ZoneInfo("Europe/Paris")  # tzdata
except Exception:
    TZ_PARIS = None


@router.get("/presence")
def get_presence(
    minutes: int = Query(5, ge=1, le=1440, description="Fenêtre 'online' en minutes"),
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
):
    now_utc = datetime.now(timezone.utc)
    threshold = now_utc - timedelta(minutes=minutes)

    subq = (
        db.query(Connection.owner_id, func.max(Connection.last_seen).label("last_seen"))
        .group_by(Connection.owner_id)
        .subquery()
    )

    rows = (
        db.query(
            User.id.label("user_id"),
            User.username,
            func.coalesce(subq.c.last_seen, None).label("last_seen"),
            User.is_admin,
        )
        .outerjoin(subq, subq.c.owner_id == User.id)
        .order_by(User.username.asc())
        .all()
    )

    out = []
    for r in rows:
        ls = r.last_seen
        if ls is not None and ls.tzinfo is None:
            ls = ls.replace(tzinfo=timezone.utc)
        out.append(
            {
                "user_id": r.user_id,
                "username": r.username,
                "online": bool(ls and ls >= threshold),
                "last_seen": ls.isoformat() if ls else None,  # UTC
                "last_seen_paris": (
                    ls.astimezone(TZ_PARIS).isoformat() if (ls and TZ_PARIS) else None
                ),
                "is_admin": bool(r.is_admin),
            }
        )

    return out
