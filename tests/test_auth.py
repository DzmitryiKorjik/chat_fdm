# Tests basiques: inscription, login, /auth/me


def test_register_and_login(api):
    r = api.register("alice", "s3cret")
    assert r.status_code in (201, 409)  # 201 si nouveau, 409 si relancé
    token = api.login("alice", "s3cret")
    me = api.me(token)
    assert me.status_code == 200
    body = me.json()
    assert body["username"] == "alice"
    assert "id" in body
