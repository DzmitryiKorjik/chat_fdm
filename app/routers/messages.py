from datetime import datetime, timezone
from typing import List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..crypto import encrypt_text, safe_decrypt
from ..database import get_db
from ..deps import get_current_user
from ..models import Message, User
from ..schemas import MessageIn, MessageOut
from ..utils_dm import is_dm_room, is_dm_room_ids, parse_dm_ids

router = APIRouter(tags=["messages"])


def _ensure_dm_access(room_id: str, current_user: User) -> None:
    """Autorisation DM: supporte dmid:<idA>:<idB> et compat dm:<alice>:<bob>."""
    # Nouveau format par IDs
    if is_dm_room_ids(room_id):
        try:
            a, b = parse_dm_ids(room_id)
        except Exception:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="room_id DM invalide"
            )
        if current_user.id not in (a, b):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à cette DM"
            )
        return

    # Ancien format par usernames (compat)
    if is_dm_room(room_id):
        try:
            _, u1, u2 = room_id.split(":")
        except ValueError:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, detail="room_id DM invalide"
            )
        if current_user.username not in (u1, u2):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN, detail="Accès refusé à cette DM"
            )
        return


@router.post("/{room_id}/messages", response_model=MessageOut, status_code=201)
def post_message(
    room_id: str,
    payload: MessageIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> MessageOut:
    _ensure_dm_access(room_id, current)
    cipher = encrypt_text(payload.content)
    msg = Message(room_id=room_id, sender_id=current.id, content=cipher)
    db.add(msg)
    db.commit()
    db.refresh(msg)
    return MessageOut(
        id=msg.id,
        room_id=msg.room_id,
        sender=current.username,
        content=safe_decrypt(msg.content),
        created_at=msg.created_at,
    )


@router.get("/{room_id}/messages", response_model=List[MessageOut])
def list_messages(
    room_id: str,
    since_ms: Optional[int] = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> List[MessageOut]:
    _ensure_dm_access(room_id, current)
    q = db.query(Message).filter(Message.room_id == room_id)
    if since_ms is not None:
        dt = datetime.fromtimestamp(since_ms / 1000.0, tz=timezone.utc)
        q = q.filter(Message.created_at > dt)
    q = q.order_by(Message.created_at.asc()).limit(max(1, min(limit, 1000)))

    out: List[MessageOut] = []
    for m in q.all():
        out.append(
            MessageOut(
                id=m.id,
                room_id=m.room_id,
                sender=m.sender.username if m.sender else str(m.sender_id),
                content=safe_decrypt(m.content),
                created_at=m.created_at,
            )
        )
    return out
