# Envoi et lecture de messages dans une room.


def test_send_and_list_messages(create_user):
    token, me = create_user("bob", "bobpass")
    # Envoi
    import time
    from datetime import datetime

    # envoie
    from fastapi.testclient import TestClient

    # POST /rooms/local/messages
    from app.crypto import encrypt_text  # juste pour vérifier en DB plus tard si besoin

    # Envoyer un message
    from app.main import app  # pour connaître le chemin

    client = TestClient(app)
    r = client.post(
        "/rooms/local/messages",
        headers={"Authorization": f"Bearer {token}"},
        json={"content": "hello world"},
    )
    assert r.status_code == 201, r.text
    created = r.json()
    assert created["room_id"] == "local"
    assert created["sender"] == me["username"]
    assert created["content"] == "hello world"

    # Lire
    r2 = client.get(
        "/rooms/local/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    msgs = r2.json()
    assert any(m["content"] == "hello world" for m in msgs)
