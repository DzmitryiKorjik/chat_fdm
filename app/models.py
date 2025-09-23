from __future__ import annotations
from datetime import datetime, timezone
from typing import List
from sqlalchemy import String, Integer, DateTime, Text, ForeignKey, Index, func, Boolean
from sqlalchemy.orm import Mapped, mapped_column, relationship
from .database import Base

class User(Base):
    """Utilisateur local (compte applicatif)."""
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    username: Mapped[str] = mapped_column(String(64), unique=True, index=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String(256), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    token_version: Mapped[int] = mapped_column(Integer, default=0)
    is_admin: Mapped[bool] = mapped_column(Boolean, default=False)  # privilèges admin

    # Relations (chargées à la demande)
    messages: Mapped[List["Message"]] = relationship(back_populates="sender", cascade="all,delete-orphan")
    connections: Mapped[list["Connection"]] = relationship(
        back_populates="owner", cascade="all,delete-orphan"
    )

class Message(Base):
    """Message textuel dans une room (canal)."""
    __tablename__ = "messages"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    room_id: Mapped[str] = mapped_column(String(128), index=True)
    sender_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    content: Mapped[str] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), index=True, default=lambda: datetime.now(timezone.utc)
    )

    # Relation inverse vers User
    sender: Mapped[User] = relationship(back_populates="messages")

# Index composé pour accélérer les timelines par room/chrono
Index("idx_messages_room_ts", Message.room_id, Message.created_at)

class Connection(Base):
    """🇫🇷 Enregistre l'activité réseau d'un utilisateur (présence/dernier accès)."""
    __tablename__ = "connections"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    owner_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    peer_id: Mapped[int | None] = mapped_column(Integer, nullable=True)  # réservé P2P (optionnel)
    transport: Mapped[str] = mapped_column(String(32), nullable=False)   # 'http' | 'websocket' | ...
    address: Mapped[str] = mapped_column(String(128), nullable=False)    # IP du client
    last_seen: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    owner: Mapped["User"] = relationship(back_populates="connections")
