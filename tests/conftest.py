# Fixtures partagées pour les tests: app, client, helpers.
import pytest
from fastapi.testclient import TestClient

from app.database import Base, engine
from app.main import app


@pytest.fixture()
def tmp_env(tmp_path, monkeypatch):
    """
    🇫🇷 Prépare un DATA_DIR éphémère + variables d'env pour UN test.
    Doit être exécuté AVANT l'import de app.main.
    """
    data_dir = tmp_path  # dossier unique par test
    db_file = data_dir / "offcom_test.db"
    key_file = data_dir / "message_key_test.key"

    monkeypatch.setenv("DATA_DIR", str(data_dir))
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    monkeypatch.setenv("MESSAGE_KEY_FILE", str(key_file))
    monkeypatch.setenv("ACCESS_TOKEN_MIN", "30")
    monkeypatch.setenv("CORS_ALLOW_ORIGINS", "*")
    yield  # aucune teardown spéciale, tmp_path sera nettoyé par pytest


@pytest.fixture()
def app_and_client(tmp_env):
    """
    Importe l'app APRÈS configuration d'env, crée les tables,
    et retourne (app, TestClient) pour UN test.
    """

    # Clean & create tables pour un état propre par test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    client = TestClient(app)
    try:
        yield app, client
    finally:
        client.close()


# ---------------- Helpers simples (API) ----------------
@pytest.fixture()
def api(app_and_client):
    """Raccourci: client + méthodes utilitaires."""
    app, client = app_and_client

    class API:
        def __init__(self, client):
            self.client = client

        def register(self, username: str, password: str, public_key: str | None = None):
            payload = {"username": username, "password": password}
            if public_key:
                payload["public_key"] = public_key
            return self.client.post("/auth/register", json=payload)

        def login(self, username: str, password: str):
            r = self.client.post("/auth/login", json={"username": username, "password": password})
            assert r.status_code == 200, r.text
            return r.json()["access_token"]

        def bearer(self, token: str):
            return {"Authorization": f"Bearer {token}"}

        def me(self, token: str):
            return self.client.get("/auth/me", headers=self.bearer(token))

    return API(client)


@pytest.fixture()
def create_user(api):
    """🇫🇷 Crée un utilisateur et renvoie (token, /auth/me)."""

    def _create(username: str, password: str, public_key: str | None = None):
        api.register(username, password, public_key=public_key)
        token = api.login(username, password)
        me = api.me(token).json()
        return token, me

    return _create


@pytest.fixture()
def promote_to_admin():
    """🇫🇷 Passe un utilisateur en admin directement en DB (pratique en tests)."""

    def _promote(user_id: int):
        from app.database import SessionLocal
        from app.models import User

        db = SessionLocal()
        try:
            u = db.query(User).filter(User.id == user_id).first()
            assert u, "user not found"
            u.is_admin = True
            db.add(u)
            db.commit()
        finally:
            db.close()

    return _promote
