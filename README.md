Petit serveur de messagerie **FastAPI** avec comptes locaux, DM (messages privés), chiffrement au repos (Fernet) et rôles admin (booléen `is_admin`).
Ce guide explique l’installation locale, le démarrage, et **un plan de tests Postman** prêt à exécuter.

---

## 1) Prérequis

* **Python 3.11+** (ok sous Windows / Linux / macOS)
* **Git** (facultatif)
* **Postman** (ou Swagger UI)
* (Optionnel) **SQLite Viewer** si vous voulez ouvrir `offcom.db`

---

## 2) Installation

```bash
  # Cloner ou copier votre projet
  git clone https://github.com/DzmitryiKorjik/chat_fdm.git 
  cd chat_fdm

  # Créer l'environnement virtuel
  python -m venv .venv
  # Activer
  #  - Windows PowerShell :
  .\.venv\Scripts\activate
  #  - Linux/macOS :
  # source .venv/bin/activate

  # Mettre à jour pip et installer les deps
  python -m pip install --upgrade pip
  pip install -r requirements.txt
```

> ⚠️ Si vous voyez un message « error reading bcrypt version », faites :
>
> ```
>   pip uninstall bcrypt passlib -y
>   pip install passlib[bcrypt]
> ```
>
>   ou `pip install --upgrade passlib`.

---

## 3) Configuration

Les valeurs par défaut conviennent pour un lancement local. Tout est centralisé dans `app/config.py`.

### Dossier de données

Par défaut, **les fichiers persistants** sont créés dans `./data/` (à côté de `app/`) :

* `data/offcom.db` — base SQLite
* `data/message_key.key` — clé Fernet (chiffrement des messages)

Vous pouvez surcharger via variables d’environnement :

* `DATA_DIR=/chemin/vers/data`
* `DATABASE_URL=sqlite:////chemin/vers/data/offcom.db`
* `MESSAGE_KEY_FILE=/chemin/vers/data/message_key.key`

## 🔑 Clé de chiffrement des messages

Lors du **premier envoi d’un message**, une clé Fernet est automatiquement générée et sauvegardée dans :

```
data/message_key.key
```

### ⚠️ Points importants

* Cette clé est **unique** pour ton instance.
* Elle permet de **déchiffrer tous les messages** stockés dans la base (`offcom.db`).
* **Ne jamais supprimer ni perdre ce fichier** : sans lui, l’historique chiffré est définitivement perdu.
* Pour déployer en production, fais une **sauvegarde sécurisée** (copie chiffrée du fichier, gestion par Vault, etc.).
* Si tu supprimes la clé, les anciens messages resteront sous forme illisible (base64 crypté).

### Paramètres utiles (env)

* `ACCESS_TOKEN_MIN` — durée des JWT d’accès (minutes, défaut **30**)
* `GLOBAL_MESSAGE_TTL_MIN` — purge DB (minutes, défaut **14400** ≃ **10 jours**)
* `HIDE_AFTER_MIN` — masquer côté API au bout de **N** minutes (défaut **10**)
* `CORS_ALLOW_ORIGINS` — origines CORS (défaut `*` en dev)

---

## 4) Démarrer le serveur local

```bash
    # Activer l'env si besoin
    .\.venv\Scripts\activate   # Windows
    # source .venv/bin/activate    # Linux/macOS
    
    # Lancer l’API
    uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

* Swagger UI : [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)
* OpenAPI JSON : [http://127.0.0.1:8000/openapi.json](http://127.0.0.1:8000/openapi.json)

---

## 5) Créer l’utilisateur root (admin)

```bash
    # Depuis la racine du projet (là où se trouve le dossier app/)
    python -m app.create_root
    # Affiche : "✅ Root user created." si créé.
    # Identifiants par défaut : username=root, password=root (à changer !)
```

## Si vous avez changé le schéma récemment (ex : ajout de `is_admin`), en dev vous pouvez réinitialiser la DB :
```bash
    > python - <<'PY'
    > from app.database import engine, Base
    > Base.metadata.drop_all(bind=engine)
    > Base.metadata.create_all(bind=engine)
    > print("✅ Schema reset")
    > PY
```

---

## 6) Modèle de données (résumé)

* **User**: `id`, `username` (unique), `password_hash`, `created_at`, `token_version`, `is_admin: bool`
* **Message**: `id`, `room_id: str`, `sender_id -> users.id`, `content: TEXT (chiffré Fernet)`, `created_at`
* **Connection**: (optionnel, carnet de pairs locaux)

**Chiffrement des messages (au repos)** :

* Stockage chiffré avec **Fernet** (clé dans `data/message_key.key`).
* Lecture côté API via `safe_decrypt` (compatible anciens messages non chiffrés).

**DM (messages privés)** :

* 2 formats pris en charge :

  * **Nouveau** par IDs : `dmid:<minId>:<maxId>`
  * **Ancien** par noms : `dm:<alice>:<bob>` (support de compatibilité)
* Autorisation : seules les 2 personnes du `room_id` peuvent lire/écrire.

---

## 7) Plan de test **Postman** (en français)

> Astuce : créez une **Collection** avec trois dossiers : `Auth`, `Messagerie`, `Admin`.
> Dans Postman, mettez votre token dans **Authorization → Bearer Token**.

### A) Authentification

1. **Inscription**

   ```
   POST http://127.0.0.1:8000/auth/register
   Body (JSON) :
   {
     "username": "Alice",
     "password": "secret123"
   }
   ```

   ✅ 201 + `id`, `username`, `created_at`

2. **Connexion**

   ```
   POST http://127.0.0.1:8000/auth/login
   Body (JSON) :
   {
     "username": "Alice",
     "password": "secret123"
   }
   ```

   ✅ 200 + `access_token`, `token_type=Bearer`, `expires_in`

3. **Profil (qui suis-je ?)**

   ```
   GET http://127.0.0.1:8000/auth/me
   Headers : Authorization: Bearer <token>
   ```

   ✅ 200 + `{ id, username, is_admin }`

> Refaire l’étape inscription/connexion pour **Bob** (ex : password « bobpass »).

---

### B) Messagerie (publique & privée)

4. **Lister les utilisateurs** (annuaire pour choisir un destinataire)

   ```
   GET http://127.0.0.1:8000/users
   Headers : Authorization: Bearer <token>
   ```

   Options :

   * `?q=bo` (filtre par fragment)
   * `?limit=50`
     ✅ 200 + liste (exclut l’utilisateur courant)

5. **Ouvrir une DM (par ID, recommandé)**
   *Il faut connaître l’`id` du destinataire (via étape 4).*

   ```
   POST http://127.0.0.1:8000/dm/open
   Headers : Authorization: Bearer <token>
   Body (JSON) :
   { "peer_id": 2 }
   ```

   ✅ 200 + `{ "room_id": "dmid:1:2" }`

   > Si vous utilisez encore l’ancien format :
   >
   > ```
   > POST /dm/open
   > { "peer_username": "Bob" }  → { "room_id": "dm:alice:bob" }
   > ```

6. **Envoyer un message dans la room**

   ```
   POST http://127.0.0.1:8000/rooms/{room_id}/messages
   Headers : Authorization: Bearer <token>
   Body (JSON) :
   { "content": "Salut 👋" }
   ```

   ✅ 201 + message en clair dans la réponse (stocké chiffré en DB)

7. **Lire les messages de la room**

   ```
   GET http://127.0.0.1:8000/rooms/{room_id}/messages
   Headers : Authorization: Bearer <token>
   ```

   Options :

   * `?since_ms=...` (timestamp en millisecondes)
   * `?limit=100`
     ✅ 200 + tableau de messages (contenu déchiffré via `safe_decrypt`)

---

### C) Administration (réservé `is_admin=true`, ex : root)

8. **Voir tous les utilisateurs (vue admin)**

   ```
   GET http://127.0.0.1:8000/admin/users
   Headers : Authorization: Bearer <admin_token>
   ```

9. **Donner les droits admin**

   ```
   POST http://127.0.0.1:8000/admin/users/{user_id}/promote
   Headers : Authorization: Bearer <admin_token>
   ```

10. **Retirer les droits admin**

    ```
    POST http://127.0.0.1:8000/admin/users/{user_id}/demote
    Headers : Authorization: Bearer <admin_token>
    ```

11. **Supprimer un utilisateur**

    ```
    DELETE http://127.0.0.1:8000/admin/users/{user_id}
    Headers : Authorization: Bearer <admin_token>
    ```

    ⚠️ Impossible de se supprimer soi-même (erreur 400).

---

## 8) Scénario rapide en **curl** (facultatif)

```bash
# Connexion Alice
TOKEN_A=$(curl -s http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"Alice","password":"secret123"}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

# Lister (sauf Alice)
curl -s http://127.0.0.1:8000/users -H "Authorization: Bearer $TOKEN_A"

# Ouvrir une DM avec l'user id=2
ROOM=$(curl -s http://127.0.0.1:8000/dm/open \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"peer_id":2}' \
  | python -c "import sys,json; print(json.load(sys.stdin)['room_id'])")
echo "room_id=$ROOM"

# Envoyer un message
curl -s http://127.0.0.1:8000/rooms/$ROOM/messages \
  -H "Authorization: Bearer $TOKEN_A" \
  -H "Content-Type: application/json" \
  -d '{"content":"Hello from Alice"}'

# Lire la DM
curl -s http://127.0.0.1:8000/rooms/$ROOM/messages -H "Authorization: Bearer $TOKEN_A"
```

---

## 9) Notes de sécurité

* **Ne jamais** connecter le Frontend directement à la base : l’admin se fait via **endpoints** sécurisés (`/admin/...`).
* La clé Fernet `message_key.key` est **sensible** : sauvegardez-la (sans elle, impossible de relire l’historique).
* En prod : réglez `CORS_ALLOW_ORIGINS` (pas de `*`), mettez HTTPS derrière **Nginx**.

---

## 10) Dépannage (FAQ)

* **405 Method Not Allowed** → vous appelez un endpoint avec la **mauvaise méthode** (ex : `GET /dm/open` au lieu de `POST`).
* **401 Unauthorized** → token manquant/expiré. Refaire `/auth/login`.
* **500 InvalidToken (Fernet)** → vieux messages non chiffrés : assurez-vous que l’API utilise **`safe_decrypt`** (déjà prévu).
* **bcrypt version warning** → (voir plus haut) `pip install passlib[bcrypt]` ou mettre à jour `passlib`.
* **Conflit de schéma (‘Table users already defined’)** → en dev, réinitialiser DB (voir §5).

---

## 11) À propos des Refresh Tokens (optionnel)

Pour éviter de se reconnecter souvent, on peut ajouter un **refresh-token** (7–30 jours) et un endpoint `/auth/refresh`.
Ce n’est **pas obligatoire** pour un chat local/offline, mais recommandé pour un usage « app publique ».
On pourra l’ajouter plus tard sans casser les clients actuels.

---

## 12) Next steps (prod rapide avec Nginx)

* Servir le Front (build SPA) via **Nginx** (`/var/www/offcom-ui`).
* Proxifier l’API sur `/api` → `http://127.0.0.1:8000`.
* Lancer FastAPI en service `systemd` (2 workers Uvicorn ou Gunicorn).

*(Quand tu seras prêt, je te donne les fichiers `nginx.conf` + `offcom.service` prêt-à-coller.)*

---




