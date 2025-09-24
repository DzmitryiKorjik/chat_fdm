# OffCom — Mini serveur de messagerie (FastAPI)

Petit serveur de messagerie **FastAPI** avec comptes locaux, DM (messages privés), **chiffrement au repos** (Fernet), rôles admin (`is_admin`), **présence/connexions**, et **clé publique utilisateur** (pour E2E côté client).
Ce guide couvre l’installation locale, la configuration, le démarrage et **un plan de tests Postman** prêt à l’emploi.

---

## 1) Prérequis

* **Python 3.11+** (Windows / Linux / macOS)
* **Postman** (ou Swagger UI intégrée)
* (Optionnel) **SQLite Viewer** pour ouvrir `offcom.db`
* (Optionnel) **Git**

---

## 2) Installation

```bash
  # Cloner ou copier le projet
    git clone https://github.com/DzmitryiKorjik/chat_fdm.git
    cd chat_fdm

    # Environnement virtuel
    python -m venv .venv

    # Activer
    # - Windows PowerShell :
    .\.venv\Scripts\activate
    # - Linux/macOS :
    # source .venv/bin/activate

    # Mettre à jour pip et installer les dépendances
    python -m pip install --upgrade pip
    pip install -r requirements.txt
```

> ⚠️ Si vous voyez « **error reading bcrypt version** » :
>
> ```bash
> pip uninstall bcrypt passlib -y
> pip install "passlib[bcrypt]" --upgrade
> ```
>
> (ou mettez à jour `passlib`).

---

## 3) Configuration

Tout est centralisé dans `app/config.py`.

### Répertoire de données

Par défaut, les fichiers persistants sont créés dans **`./data/`** (à côté de `app/`) :

* `data/offcom.db` — base **SQLite**
* `data/message_key.key` — **clé Fernet** (chiffrement au repos)

Variables d’environnement acceptées :

* `DATA_DIR=/chemin/vers/data`
* `DATABASE_URL=sqlite:////chemin/vers/data/offcom.db`
* `MESSAGE_KEY_FILE=/chemin/vers/data/message_key.key`
* `ACCESS_TOKEN_MIN` (durée JWT en minutes, défaut **30**)
* `GLOBAL_MESSAGE_TTL_MIN` (purge DB en minutes, défaut **14400** ≈ **10 jours**)
* `HIDE_AFTER_MIN` (masquer côté API après N minutes, défaut **10**)
* `CORS_ALLOW_ORIGINS` (défaut `*` en dev)

### 🔑 Clé Fernet (chiffrement des messages)

La **première fois** qu’un message est enregistré, une clé est générée dans :

```
data/message_key.key
```

**Important :**

* Cette clé est **unique** à l’instance et permet de **déchiffrer tout l’historique**.
* **Ne pas perdre** ce fichier (sinon les messages chiffrés deviennent irrécupérables).
* En prod : sauvegarder de manière **sécurisée** (Vault, backup chiffré, etc.).

---

## 4) Démarrer l’API en local

```bash
    # Activer l'env si besoin
    .\.venv\Scripts\activate   # Windows
    # source .venv/bin/activate # Linux/macOS

    # Lancer l’API
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* **Swagger UI** : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* **OpenAPI JSON** : [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5) Créer l’utilisateur root (admin)

```bash
    # Depuis la racine du projet (là où se trouve app/)
    python -m app.create_root
    # "✅ Root user created." si créé ; identifiants par défaut root/root (à changer !)
```

---

## 6) Modèle de données (résumé)

**User**

* `id`, `username` (unique), `password_hash`, `created_at`
* `token_version` (invalidation JWT par rotation)
* `is_admin: bool`
* `public_key: TEXT (nullable)` — clé publique fournie par le Front

**Message**

* `id`, `room_id: str`, `sender_id -> users.id`
* `content: TEXT` (**chiffré Fernet**)
* `created_at: datetime`

**Connection** (présence/voisinage — optionnel)

* `id`, `owner_id -> users.id`, `peer_id (nullable)`
* `transport`, `address`
* `last_seen: datetime (UTC)`

**DM (messages privés)**

* Room ID par **IDs** (recommandé) : `dmid:<minId>:<maxId>`
* Room ID par **usernames** (legacy) : `dm:<alice>:<bob>`
* Droits : seules les 2 personnes de la room peuvent lire/écrire.

---

## 7) Endpoints principaux (vue d’ensemble)

### Auth

* `POST /auth/register` — créer un compte (option : `public_key`)
* `POST /auth/login` — obtenir un JWT
* `GET  /auth/me` — profil courant

### Utilisateurs / Clés publiques

* `GET  /users` — annuaire (recherche `?q=...`)
* `PUT /users/me/public_key` — **définir/mettre à jour ma clé publique**
* `GET /users/me/public_key` — **lire ma clé publique**
* `GET /users/{user_id}/public_key` — **lire la clé d’un autre utilisateur**

### DM & Messages

* `POST /dm/open` — ouvrir une DM (par `peer_id` **ou** `peer_username`)
* `POST /rooms/{room_id}/messages` — envoyer
* `GET  /rooms/{room_id}/messages` — lister (options `since_ms`, `limit`)

### Présence / Connexions

* `GET  /presence` — liste des utilisateurs « en ligne » (pour tous les utilisateurs)
* `GET  /presence/{user_id}` — statut ciblé
* `GET  /connections` — **vue admin** détaillée (inclut IP/transport)

### Admin

* `GET    /admin/users`
* `POST   /admin/users/{id}/promote`
* `POST   /admin/users/{id}/demote`
* `DELETE /admin/users/{id}`

---

## 8) Plan de tests **Postman**

Créez une **Collection** avec les dossiers suivants. Tous les appels (sauf inscription/login) doivent inclure un **Bearer Token** valide.

### A) Authentification

1. **Inscription**

```
POST http://127.0.0.1:8000/auth/register
Body:
{
  "username": "Alice",
  "password": "secret123",
  "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----"   // optionnel
}
```

✅ 201 `{ id, username, created_at }`

2. **Connexion**

```
POST http://127.0.0.1:8000/auth/login
Body:
{ "username": "Alice", "password": "secret123" }
```

✅ 200 `{ access_token, token_type: "bearer", expires_in }`
Enregistrez `access_token` dans une variable d’environnement Postman `token`.

3. **Profil**

```
GET http://127.0.0.1:8000/auth/me
Headers: Authorization: Bearer {{token}}
```

✅ 200 `{ id, username, is_admin, ... }`

> Refaire 1–3 pour **Bob** (ex: `bobpass`).

---

### B) Utilisateurs & Clés publiques

4. **Annuaire**

```
GET http://127.0.0.1:8000/users?q=bo&limit=50
Authorization: Bearer {{token}}
```

✅ 200 : liste des utilisateurs (hors utilisateur courant)

5. **Définir ma clé publique**

```
PUT http://127.0.0.1:8000/users/me/public_key
Authorization: Bearer {{token}}
Body:
{ "public_key": "-----BEGIN PUBLIC KEY-----\n...\n-----END PUBLIC KEY-----" }
```

✅ 200 `{ user_id, username, public_key }`

6. **Lire ma clé publique**

```
GET http://127.0.0.1:8000/users/me/public_key
Authorization: Bearer {{token}}
```

✅ 200 `{ user_id, username, public_key }`

7. **Lire la clé de Bob (id=2)**

```
GET http://127.0.0.1:8000/users/2/public_key
Authorization: Bearer {{token}}
```

✅ 200 `{ user_id: 2, username: "Bob", public_key: "..." }`

---

### C) DM & Messages

8. **Ouvrir une DM avec Bob**

```
POST http://127.0.0.1:8000/dm/open
Authorization: Bearer {{token}}
Body:
{ "peer_id": 2 }    // ou { "peer_username": "Bob" }
```

✅ 200 `{ "room_id": "dmid:1:2" }`

9. **Envoyer un message**

```
POST http://127.0.0.1:8000/rooms/dmid:1:2/messages
Authorization: Bearer {{token}}
Body:
{ "content": "Salut Bob 👋" }
```

✅ 201 `{ id, room_id, sender, content (en clair), created_at }`

10. **Lire la conversation**

```
GET http://127.0.0.1:8000/rooms/dmid:1:2/messages?limit=50
Authorization: Bearer {{token}}
```

✅ 200 `[ { id, sender, content (décrypté), created_at }, ... ]`

---

### D) Présence & Connexions

11. **Présence (publique) — qui est en ligne ?**

```
GET http://127.0.0.1:8000/presence?minutes=30
Authorization: Bearer {{token}}
```

✅ 200 : tableau `{ user_id, username, online: true, last_seen, last_seen_paris }`

12. **Présence d’un utilisateur**

```
GET http://127.0.0.1:8000/presence/2?minutes=30
Authorization: Bearer {{token}}
```

✅ 200 `{ user_id, username, online: true/false, ... }`

13. **Connexions (vue admin)**

```
GET http://127.0.0.1:8000/connections?minutes=60
Authorization: Bearer {{admin_token}}
```

✅ 200 : tableau `{ owner_id, transport, address, last_seen, last_seen_paris }`
❌ 403 si token non admin (comportement attendu).

---

### E) Administration

14. **Lister tous les utilisateurs**

```
GET http://127.0.0.1:8000/admin/users
Authorization: Bearer {{admin_token}}
```

15. **Donner les droits admin à un user**

```
POST http://127.0.0.1:8000/admin/users/2/promote
Authorization: Bearer {{admin_token}}
```

16. **Retirer les droits admin**

```
POST http://127.0.0.1:8000/admin/users/2/demote
Authorization: Bearer {{admin_token}}
```

17. **Supprimer un utilisateur**

```
DELETE http://127.0.0.1:8000/admin/users/2
Authorization: Bearer {{admin_token}}
```

⚠️ Impossible de supprimer son propre compte (root).

---

## 9) Scénario rapide en `curl` (facultatif)

```bash
# Connexion Alice
TOKEN_A=$(curl -s http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Alice","password":"secret123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)["'"'access_token'"'"])")

# Lister (sauf Alice)
curl -s http://127.0.0.1:8000/users -H "Authorization: Bearer $TOKEN_A"

# Ouvrir une DM avec l'user id=2
ROOM=$(curl -s http://127.0.0.1:8000/dm/open \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"peer_id":2}' \
  | python -c "import sys,json; print(json.load(sys.stdin)["'"'room_id'"'"])")

# Envoyer un message
curl -s http://127.0.0.1:8000/rooms/$ROOM/messages \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello from Alice"}'

# Lire la DM
curl -s http://127.0.0.1:8000/rooms/$ROOM/messages -H "Authorization: Bearer $TOKEN_A"
```

---

## 10) Sécurité & bonnes pratiques

* **Ne jamais** connecter le Frontend directement à la base : admin via **API** uniquement.
* La **clé Fernet** `message_key.key` est sensible : sauvegarde sécurisée obligatoire.
* En prod : pas de CORS `*`, HTTPS derrière **Nginx**, JWT courts (ex. 15–30 min).
* Possibilité d’ajouter un **refresh token** (7–30 jours) + `/auth/refresh` (optionnel).

---

## 11) Dépannage (FAQ)

* **405 Method Not Allowed** → mauvaise méthode HTTP (ex. `GET /dm/open` au lieu de `POST`).
* **401 Unauthorized** → token manquant/expiré → refaire `/auth/login`.
* **403 Forbidden** → endpoint admin avec token utilisateur (ex. `/connections`).
* **500 InvalidToken (Fernet)** → anciens messages non chiffrés : l’API utilise `safe_decrypt` (compatibilité).
* **bcrypt warning** → voir §2 (passlib\[bcrypt]).
* **Schéma en conflit** → en dev, reset DB (cf. §5) ou migration SQLite simple (ALTER TABLE …).

---

## 12) Déploiement rapide (Nginx + service)

* Servir le Front (SPA) via **Nginx**, ex. `/var/www/offcom-ui`.
* Proxy API `/api` → `http://127.0.0.1:8000`.
* Lancer FastAPI via `systemd` (Uvicorn/Gunicorn, 2 workers).
  *(Contacte-moi quand tu es prêt : je te donnerai `nginx.conf` et `offcom.service` prêts à coller.)*

---
