""" Utilitaires de chiffrement pour le contenu des messages (au repos).
- Fernet (cryptography) garantit confidentialité + intégrité.
- Le token chiffré est une chaîne base64 URL-safe, stockable en TEXT.
"""
from __future__ import annotations
from cryptography.fernet import Fernet
from .config import MESSAGE_KEY_FILE
from cryptography.fernet import InvalidToken
import os

_FERNET: Fernet | None = None

def _load_or_create_key(path: str) -> bytes:
    """ Charge la clé depuis le fichier, sinon la crée et la sauvegarde.
    Conservez ce fichier en lieu sûr : sans la clé, impossible de déchiffrer l'historique.
    """
    if os.path.exists(path):
        with open(path, "rb") as f:
            return f.read().strip()
    key = Fernet.generate_key()
    with open(path, "wb") as f:
        f.write(key)
    return key

def _get_fernet() -> Fernet:
    global _FERNET
    if _FERNET is None:
        _FERNET = Fernet(_load_or_create_key(MESSAGE_KEY_FILE))
    return _FERNET

def encrypt_text(plaintext: str) -> str:
    """ Chiffre du texte clair en token base64 (str)."""
    return _get_fernet().encrypt(plaintext.encode("utf-8")).decode("utf-8")

def decrypt_text(token_str: str) -> str:
    """ Déchiffre un token base64 (str) vers texte clair."""
    return _get_fernet().decrypt(token_str.encode("utf-8")).decode("utf-8")

def safe_decrypt(token_str: str) -> str:
    """Essaye de déchiffrer, retourne brut si erreur (compat ancien data)."""
    try:
        return decrypt_text(token_str)
    except (InvalidToken, Exception):
        # on renvoie le contenu brut si ce n'était pas du Fernet
        return token_str
