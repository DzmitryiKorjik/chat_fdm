from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from ..crypto import encrypt_text, safe_decrypt
from ..database import get_db
from ..deps import get_current_user
from ..models import Message, User
from ..schemas import MessageIn, MessageOutDetailed
from ..utils_dm import is_dm_room, is_dm_room_ids, parse_dm_ids, peer_id_for_sender

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


@router.get("/my-rooms", response_model=list[str])
def list_user_rooms(
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[str]:
    """
    Retourne la liste des room_id où l'utilisateur courant est **participant**.
    - DM par IDs (nouveau format) : dmid:<minId>:<maxId>
      -> on récupère toutes les rooms qui contiennent l'id courant d'un côté ou de l'autre
    - DM par usernames (ancien format compat) : dm:<alice>:<bob>
      -> idem avec le username courant
    - Bonus : inclure aussi les rooms où l'utilisateur a posté (ex: 'local'),
      pour que le front voie ses fils de discussion "non-DM".
    """
    uid = current.id
    uname = current.username

    # Modèles DM
    dmid_left = f"dmid:{uid}:%"
    dmid_right = f"dmid:%:{uid}"
    dm_left = f"dm:{uname}:%"
    dm_right = f"dm:%:{uname}"

    rows = (
        db.query(Message.room_id)
        .filter(
            or_(
                # DMs (nouveau format par IDs)
                Message.room_id.like(dmid_left),
                Message.room_id.like(dmid_right),
                # DMs (ancien format par usernames)
                Message.room_id.like(dm_left),
                Message.room_id.like(dm_right),
                # Autres rooms où l'utilisateur a posté
                Message.sender_id == uid,
            )
        )
        .distinct()
        .all()
    )

    # rows = [(room_id,), ...] -> on aplatit en liste de str
    return [r[0] for r in rows]


@router.post("/{room_id}/messages", response_model=MessageOutDetailed, status_code=201)
def post_message(
    room_id: str,
    payload: MessageIn,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> MessageOutDetailed:
    _ensure_dm_access(room_id, current)
    msg = Message(room_id=room_id, sender_id=current.id, content=encrypt_text(payload.content))
    db.add(msg)
    db.commit()
    db.refresh(msg)
    # Pour DM, on déduit le recipient_id (peer) du room_id et de l'id courant
    try:
        recipient_id = peer_id_for_sender(room_id, current.id)
    except ValueError:
        # Pas une DM, ou format inconnu (ex: 'local') -> on met 0
        recipient_id = 0

    return MessageOutDetailed(
        id=msg.id,
        room_id=msg.room_id,
        sender=current.username,
        sender_id=current.id,
        recipient_id=recipient_id,
        content=payload.content,  # в ответ отдаем в открытом виде
        created_at=msg.created_at,
    )


@router.get("/{room_id}/messages", response_model=list[MessageOutDetailed])
def list_messages(
    room_id: str,
    since_ms: int | None = None,
    limit: int = 100,
    db: Session = Depends(get_db),
    current: User = Depends(get_current_user),
) -> list[MessageOutDetailed]:
    _ensure_dm_access(room_id, current)
    q = db.query(Message).filter(Message.room_id == room_id)
    if since_ms:
        q = q.filter(Message.created_at >= datetime.fromtimestamp(since_ms / 1000, tz=timezone.utc))
    msgs = q.order_by(Message.created_at.asc()).limit(max(1, min(limit, 500))).all()

    # Détecter si c'est une DM par IDs pour déduire le recipient_id
    try:
        a, b = parse_dm_ids(room_id)
        is_dm = True
    except ValueError:
        is_dm = False
        a = b = 0

    out: list[MessageOutDetailed] = []
    for m in msgs:
        # name de l'expéditeur
        sender_user = db.get(User, m.sender_id)
        sender_name = sender_user.username if sender_user else f"user:{m.sender_id}"
        # tenter de décrypter le contenu
        try:
            content = safe_decrypt(m.content)
        except Exception:
            content = m.content

        # recipient_id (peer) si DM par IDs
        if is_dm:
            recipient_id = b if m.sender_id == a else a
        else:
            recipient_id = 0

        out.append(
            MessageOutDetailed(
                id=m.id,
                room_id=m.room_id,
                sender=sender_name,
                sender_id=m.sender_id,
                recipient_id=recipient_id,
                content=content,
                created_at=m.created_at,
            )
        )
    return out
