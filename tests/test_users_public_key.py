# Déclaration / lecture de la clé publique.

PEM = (
    "-----BEGIN PUBLIC KEY-----\nMFYwEAYHKoZIzj0CAQYFK4EEAAoDQgAE9s4Xg...\n-----END PUBLIC KEY-----"
)


def test_set_and_get_public_key(create_user):
    token, me = create_user("carol", "carolpw")

    # Déclarer sa clé
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    r = client.put(
        "/users/me/public_key",
        headers={"Authorization": f"Bearer {token}"},
        json={"public_key": PEM},
    )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["user_id"] == me["id"]
    assert "PUBLIC KEY" in body["public_key"]

    # Lire sa clé
    r2 = client.get(
        "/users/me/public_key",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200
    assert "PUBLIC KEY" in r2.json()["public_key"]

    # Un autre user peut lire la clé de carol
    token2, me2 = create_user("dave", "davepw")
    r3 = client.get(
        f"/users/{me['id']}/public_key",
        headers={"Authorization": f"Bearer {token2}"},
    )
    assert r3.status_code == 200
    assert r3.json()["public_key"] == PEM
