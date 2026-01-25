"""Helpers for encrypting sensitive text at rest."""

from __future__ import annotations

from cryptography.fernet import Fernet, InvalidToken

from lykke.core.config import settings

ENCRYPTION_PREFIX = "enc:"


def _get_fernet() -> Fernet:
    key = settings.BRAIN_DUMP_ENCRYPTION_KEY
    if not key:
        raise RuntimeError(
            "BRAIN_DUMP_ENCRYPTION_KEY is required to encrypt brain dumps."
        )
    try:
        return Fernet(key)
    except Exception as exc:  # pragma: no cover - defensive configuration guard
        raise RuntimeError(
            "BRAIN_DUMP_ENCRYPTION_KEY must be a valid Fernet key."
        ) from exc


def encrypt_text(value: str | None) -> str | None:
    """Encrypt plaintext into a prefixed ciphertext string."""
    if value is None:
        return None
    if value.startswith(ENCRYPTION_PREFIX):
        return value
    fernet = _get_fernet()
    token = fernet.encrypt(value.encode("utf-8")).decode("utf-8")
    return f"{ENCRYPTION_PREFIX}{token}"


def decrypt_text(value: str | None) -> str | None:
    """Decrypt a prefixed ciphertext string, or pass through plaintext."""
    if value is None:
        return None
    if not value.startswith(ENCRYPTION_PREFIX):
        return value
    fernet = _get_fernet()
    token = value[len(ENCRYPTION_PREFIX) :]
    try:
        return fernet.decrypt(token.encode("utf-8")).decode("utf-8")
    except InvalidToken as exc:
        raise RuntimeError("Failed to decrypt brain dump content.") from exc
