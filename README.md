# Plan de test API (Postman)

## Authentification

1. **Inscription (nouvel utilisateur)**

   ```
   POST /auth/register
   Corps (JSON): 
   {
     "username": "Alice",
     "password": "secret123"
   }
   ```

   ✅ Retourne : `id`, `username`, `created_at`.

2. **Connexion (login)**

   ```
   POST /auth/login
   Corps (JSON): 
   {
     "username": "Alice",
     "password": "secret123"
   }
   ```

   ✅ Retourne : `access_token`.
   👉 Copie ce token et mets-le dans Postman → **Authorization → Bearer Token**.

3. **Mon profil**

   ```
   GET /auth/me
   Header: Authorization: Bearer <token>
   ```

   ✅ Retourne : `id`, `username`, `is_admin`.

---

## Messagerie

4. **Lister les utilisateurs (pour voir qui existe)**

   ```
   GET /users
   Header: Authorization: Bearer <token>
   ```

   ✅ Retourne la liste de tous les utilisateurs (sauf toi-même).

5. **Ouvrir une discussion privée (DM)**

   ```
   POST /dm/open
   Header: Authorization: Bearer <token>
   Corps (JSON):
   {
     "peer_username": "Bob"
   }
   ```

   ✅ Retourne `room_id` (exemple : `alice:bob`).

6. **Envoyer un message**

   ```
   POST /rooms/{room_id}/messages
   Header: Authorization: Bearer <token>
   Corps (JSON):
   {
     "content": "Salut Bob"
   }
   ```

   ✅ Retourne le message : `id`, `sender`, `content`, `created_at`.

7. **Lire l’historique des messages**

   ```
   GET /rooms/{room_id}/messages
   Header: Authorization: Bearer <token>
   ```

   ✅ Retourne la conversation (messages en clair via `safe_decrypt`).

---

## Administration (réservé aux admins / root)

8. **Lister tous les utilisateurs**

   ```
   GET /admin/users
   Header: Authorization: Bearer <admin_token>
   ```

9. **Donner les droits admin**

   ```
   POST /admin/users/{id}/promote
   Header: Authorization: Bearer <admin_token>
   ```

10. **Retirer les droits admin**

```
POST /admin/users/{id}/demote
Header: Authorization: Bearer <admin_token>
```

11. **Supprimer un utilisateur**

```
DELETE /admin/users/{id}
Header: Authorization: Bearer <admin_token>
```

