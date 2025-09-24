from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from ..database import get_db
from ..deps import get_current_user
from ..models import User
from ..schemas import OpenDMRequest, OpenDMResponse
from ..utils_dm import canonical_dm_room_ids

router = APIRouter(tags=["dm"])


@router.post("/open", response_model=OpenDMResponse)
def open_dm(
    payload: OpenDMRequest,
    db: Session = Depends(get_db),
    current=Depends(get_current_user),
) -> OpenDMResponse:
    """Ouvre (ou récupère) une DM par IDs et renvoie son room_id (dmid:a:b)."""
    if payload.peer_id == current.id:
        raise HTTPException(status_code=400, detail="Impossible d'ouvrir une DM avec soi-même")
    peer = db.query(User).get(payload.peer_id)
    if not peer:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur introuvable")
    room_id = canonical_dm_room_ids(current.id, peer.id)
    return OpenDMResponse(room_id=room_id)
