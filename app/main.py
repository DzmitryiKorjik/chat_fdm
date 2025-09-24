from __future__ import annotations

import asyncio
import contextlib
import logging
import os
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone
from ipaddress import ip_address

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .config import CORS_ALLOW_ORIGINS, GLOBAL_MESSAGE_TTL_MIN
from .database import Base, SessionLocal, engine
from .models import Message
from .routers import auth as auth_router
from .routers import connections as connections_router
from .routers import dm as dm_router
from .routers import messages as messages_router
from .routers import users as users_router

logger = logging.getLogger(__name__)

# ─────────────────────────────────────────────────────────────────────────────
# Tâche périodique : purge des messages au-delà du TTL global
# ─────────────────────────────────────────────────────────────────────────────
async def _cleanup_loop() -> None:
    """Supprime périodiquement les messages plus vieux que GLOBAL_MESSAGE_TTL_MIN minutes."""
    if GLOBAL_MESSAGE_TTL_MIN <= 0:
        return  # TTL désactivé
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
        except Exception as exc:
            # On ne tue pas la boucle pour une erreur ponctuelle
            logger.error("Erreur dans la tâche de nettoyage: %s", exc, exc_info=True)
        # Cadence : 1 fois / heure
        await asyncio.sleep(3600)

# ─────────────────────────────────────────────────────────────────────────────
# Lifespan FastAPI (remplace les anciens @app.on_event)
# ─────────────────────────────────────────────────────────────────────────────
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Démarrage
    Base.metadata.create_all(bind=engine)
    task = asyncio.create_task(_cleanup_loop())
    try:
        yield
    finally:
        # Arrêt propre de la tâche
        task.cancel()
        with contextlib.suppress(asyncio.CancelledError):
            await task

# ─────────────────────────────────────────────────────────────────────────────
# Application
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="OffCom Backend",
    version="0.1.0",
    description="Backend minimal (offline-first) pour utilisateurs, messages et connexions",
    lifespan=lifespan,
)

# CORS (large en dev)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routeurs (attention à ne pas re-préfixer dans main si déjà préfixés dans chaque routeur)
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(messages_router.router, prefix="/rooms", tags=["messages"])
app.include_router(connections_router.router, prefix="/connections", tags=["connections"])
app.include_router(users_router.router)  # le routeur a déjà prefix="/users"
app.include_router(dm_router.router, prefix="/dm", tags=["dm"])

# UI statique facultative (si app/../web existe) -> /ui
_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(_web_dir):
    app.mount("/ui", StaticFiles(directory=_web_dir, html=True), name="ui")

# ─────────────────────────────────────────────────────────────────────────────
# Lancement direct en dev
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    bind_host = os.getenv("APP_HOST", "127.0.0.1")
    bind_port = int(os.getenv("APP_PORT", "8000"))
    reload_enabled = os.getenv("RELOAD", "true").lower() == "true"

    # Avertir si on écoute sur "toutes interfaces" (ipv4 0.0.0.0 ou ipv6 ::)
    try:
        if ip_address(bind_host).is_unspecified:
            logger.warning(
                "Binding sur toutes interfaces (%s) : "
                "assurez-vous d'être derrière un proxy et d'avoir durci la conf.",
                bind_host,
            )
    except ValueError:
        # si HOST est un hostname (ex: 'localhost'), on ne bloque pas
        pass

    uvicorn.run("app.main:app", host=bind_host, port=bind_port, reload=reload_enabled)
