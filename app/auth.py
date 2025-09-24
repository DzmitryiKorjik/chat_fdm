from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import uuid4

import jwt
from fastapi import HTTPException, status
from jwt import PyJWTError
from passlib.context import CryptContext

from .config import ACCESS_TOKEN_EXPIRE_MINUTES, ALGORITHM, SECRET_KEY

# Contexte de hashage (bcrypt)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def get_password_hash(password: str) -> str:
    """Hache un mot de passe en utilisant bcrypt."""
    return pwd_context.hash(password)


def verify_password(plain_password: str, password_hash: str) -> bool:
    """Vérifie qu'un mot de passe correspond au hash stocké."""
    return pwd_context.verify(plain_password, password_hash)


def create_access_token(
    subject: str, user_token_version: int, expires_delta: Optional[timedelta] = None
) -> str:
    """Crée un JWT avec identifiant unique (jti) et version de jeton (ver)."""
    now = datetime.now(timezone.utc)
    expire = now + (expires_delta or timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES))
    to_encode = {
        "sub": subject,  # identifiant logique (username)
        "ver": user_token_version,  # version côté serveur
        "jti": str(uuid4()),  # id unique du jeton
        "iat": int(now.timestamp()),
        "exp": int(expire.timestamp()),
    }
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> str:
    """Décode et valide un JWT, renvoie le subject (username)."""
    try:
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        return str(payload.get("sub"))
    except PyJWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Token invalide ou expiré"
        )
