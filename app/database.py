from __future__ import annotations

from typing import Generator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, sessionmaker

from .config import DATABASE_URL

# Création du moteur SQLAlchemy
# - future=True = nouvelle API
# - echo=False = pas de log SQL (mettre True en debug)
# - check_same_thread=False = obligatoire pour SQLite en mode multi-threads
engine = create_engine(
    DATABASE_URL,
    future=True,
    echo=False,
    connect_args={"check_same_thread": False} if DATABASE_URL.startswith("sqlite") else {},
)

# Fabrique de sessions : une session par requête HTTP
SessionLocal = sessionmaker(
    bind=engine,
    expire_on_commit=False,  # garde les objets utilisables après commit
    autoflush=False,
)


# Classe de base pour tous les modèles ORM
class Base(DeclarativeBase):
    """Base déclarative dont héritent tous les modèles ORM."""

    pass


# Dépendance FastAPI : ouvre/ferme une session DB par requête
def get_db() -> Generator:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
