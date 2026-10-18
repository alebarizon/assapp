"""Cifra simétrica para credenciais guardadas no banco (chave derivada do SECRET_KEY)."""
import base64
import hashlib

from cryptography.fernet import Fernet, InvalidToken
from django.conf import settings


def _fernet() -> Fernet:
    chave = hashlib.sha256(f"payments:{settings.SECRET_KEY}".encode()).digest()
    return Fernet(base64.urlsafe_b64encode(chave))


def cifrar(texto: str) -> str:
    return _fernet().encrypt(texto.encode()).decode()


def decifrar(cifrado: str) -> str:
    """Texto vazio se não houver valor ou se o SECRET_KEY mudou desde que foi cifrado."""
    if not cifrado:
        return ""
    try:
        return _fernet().decrypt(cifrado.encode()).decode()
    except InvalidToken:
        return ""
