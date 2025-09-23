"""Script utilitaire : créer l'utilisateur root (admin) s'il n'existe pas."""
from __future__ import annotations

# IMPORTANT — ce bloc doit être AVANT tout import relatif (from .xxx import ...)
import sys, os
if __name__ == "__main__" and __package__ is None:
    # ➜ ajoute le répertoire racine du projet dans sys.path et définit le package
    sys.path.append(os.path.dirname(os.path.dirname(__file__)))
    __package__ = "app"

# Imports relatifs (fonctionneront maintenant en mode script)
from .database import SessionLocal, engine, Base
from .models import User
from .auth import get_password_hash


def main() -> None:
    """Crée le compte root (admin) si absent."""
    #Crée les tables si besoin
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
