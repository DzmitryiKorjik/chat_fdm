"""Script utilitaire : créer l'utilisateur root (admin) s'il n'existe pas."""

from __future__ import annotations

import os

# IMPORTANT — ce bloc doit être AVANT tout import relatif (from .xxx import ...)
import sys

if __name__ == "__main__" and __package__ is None:
    # ➜ ajoute le répertoire racine du projet dans sys.path et définit le package
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    __package__ = "app"

from .auth import get_password_hash

# Imports relatifs (fonctionneront maintenant en mode script)
from .database import Base, SessionLocal, engine
from .models import User


def main() -> None:
    """Crée le compte root (admin) si absent."""
    # Crée les tables si besoin
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # Vérifie si 'root' existe déjà
        exists = db.query(User).filter(User.username == "root").first()
        if exists:
            print("Root existe déjà.")
            return

        # Crée le compte root avec privilèges admin
        root = User(
            username="root",
            password_hash=get_password_hash("rootazerty"),  # changez le mot de passe ensuite
            is_admin=True,
        )
        db.add(root)
        db.commit()
        print(" Root user created.")
    finally:
        db.close()


if __name__ == "__main__":
    main()
