"""Criptografia de tokens em repouso (Fernet). Chave vem SOMENTE do .env."""
from functools import lru_cache

from cryptography.fernet import Fernet, InvalidToken

from app.core.config import settings


@lru_cache(maxsize=1)
def _fernet() -> Fernet:
    key = settings.MELHOR_ENVIO_TOKEN_ENCRYPTION_KEY
    if not key:
        raise RuntimeError("MELHOR_ENVIO_TOKEN_ENCRYPTION_KEY não configurada")
    return Fernet(key.encode() if isinstance(key, str) else key)


def encrypt(value: str) -> str:
    if value is None:
        return None
    return _fernet().encrypt(value.encode()).decode()


def decrypt(value: str) -> str:
    if not value:
        return None
    try:
        return _fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None


@lru_cache(maxsize=1)
def _mp_fernet() -> Fernet:
    key = settings.MERCADO_PAGO_TOKEN_ENCRYPTION_KEY
    if not key:
        raise RuntimeError("MERCADO_PAGO_TOKEN_ENCRYPTION_KEY não configurada")
    return Fernet(key.encode() if isinstance(key, str) else key)


def mp_encrypt(value: str) -> str:
    if value is None:
        return None
    return _mp_fernet().encrypt(value.encode()).decode()


def mp_decrypt(value: str) -> str:
    if not value:
        return None
    try:
        return _mp_fernet().decrypt(value.encode()).decode()
    except InvalidToken:
        return None
