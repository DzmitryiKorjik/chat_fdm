from __future__ import annotations

import os
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .database import Base, engine, SessionLocal
from .models import Message
from .config import CORS_ALLOW_ORIGINS, GLOBAL_MESSAGE_TTL_MIN

# Routers
from .routers import auth as auth_router
from .routers import messages as messages_router
from .routers import connections as connections_router
from .routers import users as users_router
from .routers import dm as dm_router

app = FastAPI(
    title="OffCom Backend",
    version="0.1.0",
    description="Backend minimal (offline-first) pour utilisateurs, messages et connexions",
)

# CORS (large en dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Brancher les routeurs
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(messages_router.router, prefix="/rooms", tags=["messages"])
app.include_router(connections_router.router, prefix="/connections", tags=["connections"])
app.include_router(users_router.router, tags=["users"])
app.include_router(dm_router.router, prefix="/dm", tags=["dm"])

# UI statique facultative (si app/../web existe) -> /ui
_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(_web_dir):
    app.mount("/ui", StaticFiles(directory=_web_dir, html=True), name="ui")

# ── Tâche périodique : purge des messages au-delà du TTL global ──────────────
async def _cleanup_loop() -> None:
    """Supprime périodiquement les messages plus vieux que GLOBAL_MESSAGE_TTL_MIN minutes."""
    if GLOBAL_MESSAGE_TTL_MIN <= 0:
        return
    while True:
        try:
            db = SessionLocal()
            try:
                deadline = datetime.now(timezone.utc) - timedelta(minutes=GLOBAL_MESSAGE_TTL_MIN)
                deleted = (
                    db.query(Message)
                    .filter(Message.created_at <= deadline)
                    .delete(synchronize_session=False)
                )
                if deleted:
                    db.commit()
            finally:
                db.close()
        except Exception:
            # ne pas tuer la boucle en cas d'erreur ponctuelle
            pass
        await asyncio.sleep(3600)  # 1 fois / heure

# Événements d'application
@app.on_event("startup")
async def on_startup() -> None:
    """Crée les tables et lance la purge si activée."""
    Base.metadata.create_all(bind=engine)
    # lancer la boucle sans bloquer
    asyncio.create_task(_cleanup_loop())

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
