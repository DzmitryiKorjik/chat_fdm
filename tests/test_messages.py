# Envoi et lecture de messages dans une room.


def test_send_and_list_messages(create_user, app_and_client):
    token, me = create_user("bob", "bobpass")
    _, client = app_and_client

    # Envoi
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

    # Lecture
    r2 = client.get(
        "/rooms/local/messages",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert r2.status_code == 200, r2.text
    msgs = r2.json()
    assert any(m["content"] == "hello world" for m in msgs)
