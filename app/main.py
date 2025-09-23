from __future__ import annotations

import os
import asyncio
from datetime import datetime, timezone, timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Base / moteur / sessions DB
from .database import Base, engine, SessionLocal

# Modèles utilisés par la tâche de nettoyage
from .models import Message

# Configuration (CORS + TTL)
from .config import CORS_ALLOW_ORIGINS, GLOBAL_MESSAGE_TTL_MIN

# Routeurs (endpoints appelés par le frontend)
from .routers import auth as auth_router
from .routers import messages as messages_router
from .routers import connections as connections_router
from .routers import users as users_router
from .routers import dm as dm_router


# ─────────────────────────────────────────────────────────────────────────────
# Création de l'application FastAPI
# ─────────────────────────────────────────────────────────────────────────────
app = FastAPI(
    title="OffCom Backend",
    version="0.1.0",
    description="Backend minimal (offline-first) pour utilisateurs, messages et connexions",
)

# CORS permissif en dev (restreindre en production)
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ALLOW_ORIGINS,  # ex: ["http://localhost:5173"]
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ─────────────────────────────────────────────────────────────────────────────
# Branche les routeurs
# ─────────────────────────────────────────────────────────────────────────────
app.include_router(auth_router.router, prefix="/auth", tags=["auth"])
app.include_router(messages_router.router, prefix="/rooms", tags=["messages"])
app.include_router(connections_router.router, prefix="/connections", tags=["connections"])
app.include_router(users_router.router)
app.include_router(dm_router.router, prefix="/dm")

# ─────────────────────────────────────────────────────────────────────────────
# Optionnel : monter une petite UI statique si le dossier web/ existe
#    -> Accessible via http://localhost:8000/ui/
# ─────────────────────────────────────────────────────────────────────────────
_web_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "web"))
if os.path.isdir(_web_dir):
    app.mount("/ui", StaticFiles(directory=_web_dir, html=True), name="ui")


# ─────────────────────────────────────────────────────────────────────────────
# Tâche de fond : purge périodique des messages trop anciens (TTL)
# - GLOBAL_MESSAGE_TTL_MIN = durée de rétention en minutes (ex: 10 jours = 14400)
# - Si TTL <= 0, la purge est désactivée.
# ─────────────────────────────────────────────────────────────────────────────
async def _cleanup_loop() -> None:
    """Supprime périodiquement les messages plus vieux que GLOBAL_MESSAGE_TTL_MIN minutes."""
    if GLOBAL_MESSAGE_TTL_MIN <= 0:
        return  # TTL désactivé -> on ne lance pas la boucle
    while True:
        try:
            db = SessionLocal()
            deadline = datetime.now(timezone.utc) - timedelta(minutes=GLOBAL_MESSAGE_TTL_MIN)
            # suppression en base (physique) des messages au-delà du TTL global
            deleted = db.query(Message).filter(Message.created_at <= deadline).delete(synchronize_session=False)
            if deleted:
                db.commit()
            db.close()
        except Exception:
            # On ignore les erreurs ponctuelles pour ne pas tuer la boucle
            pass

        # cadence de nettoyage : 1 fois par heure suffit
        await asyncio.sleep(3600)


# ─────────────────────────────────────────────────────────────────────────────
# Événements d'application
# ─────────────────────────────────────────────────────────────────────────────
@app.on_event("startup")
def on_startup() -> None:
    """Au démarrage :
    - crée les tables si besoin
    - lance la tâche de nettoyage en arrière-plan (si TTL activé)
    """
    Base.metadata.create_all(bind=engine)

    # Lancement de la boucle de purge sans bloquer le serveur
    loop = asyncio.get_event_loop()
    loop.create_task(_cleanup_loop())


# ─────────────────────────────────────────────────────────────────────────────
# Démarrage direct (utile en dev) : python -m app.main
# ─────────────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    import uvicorn

    # 🇫🇷 Démarrage pratique pour le développement
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000, reload=True)
