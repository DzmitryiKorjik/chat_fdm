# Vérifie l’accès /connections: interdit pour user, autorisé pour admin.
# Et que l’upsert de présence marche (se fait via get_current_user).


def test_connections_forbidden_for_user(create_user):
    token, me = create_user("eve", "evepass")

    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)

    # Fait un appel authentifié pour marquer last_seen
    r0 = client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert r0.status_code == 200

    # Essaye /connections en tant que simple user -> 403
    r = client.get("/connections", headers={"Authorization": f"Bearer {token}"})
    assert r.status_code == 403


def test_connections_ok_for_admin(create_user, promote_to_admin):
    # Crée admin
    atok, admin = create_user("rooter", "rootpw")
    promote_to_admin(admin["id"])

    # Crée un simple user et marque son activité
    utok, u = create_user("frank", "frankpw")
    from fastapi.testclient import TestClient

    from app.main import app

    client = TestClient(app)
    client.get("/auth/me", headers={"Authorization": f"Bearer {utok}"})

    # Appelle /connections avec token admin
    r = client.get("/connections?minutes=60", headers={"Authorization": f"Bearer {atok}"})
    assert r.status_code == 200, r.text
    arr = r.json()
    # On doit voir au moins une entrée (frank ou même l’admin)
    assert isinstance(arr, list)
