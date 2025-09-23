from __future__ import annotations
import os

# JWT
SECRET_KEY: str = os.getenv("SECRET_KEY", "dev-secret-change-me")
ALGORITHM: str = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_MIN", "30")) # 30 min

# Répertoires (par défaut: ../data/ à côté de app/)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))              # .../app
PROJECT_ROOT = os.path.dirname(BASE_DIR)                           # .../
DATA_DIR = os.getenv("DATA_DIR", os.path.join(PROJECT_ROOT, "data"))
os.makedirs(DATA_DIR, exist_ok=True)

#️ Fichiers persistants
DATABASE_URL = os.getenv("DATABASE_URL", f"sqlite:///{os.path.join(DATA_DIR, 'offcom.db')}")
MESSAGE_KEY_FILE = os.getenv("MESSAGE_KEY_FILE", os.path.join(DATA_DIR, "message_key.key"))

# CORS (en dev on autorise tout, à restreindre en prod)
CORS_ALLOW_ORIGINS = os.getenv("CORS_ALLOW_ORIGINS", "*").split(",")

# Politiques de rétention/affichage
DELETE_AFTER_READ_FOR_ALL: bool = os.getenv("DELETE_AFTER_READ_FOR_ALL", "false").lower() == "true"
HIDE_AFTER_MIN: int = int(os.getenv("HIDE_AFTER_MIN", "10"))           # masquer dans l'API après 10 min
GLOBAL_MESSAGE_TTL_MIN: int = int(os.getenv("GLOBAL_MESSAGE_TTL_MIN", "14400"))  # purge DB après 10 jours
