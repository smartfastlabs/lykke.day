"""Utilities for SMS login code hashing and verification."""

import hashlib
import hmac
import secrets

from lykke.core.config import settings


def generate_code(length: int = 6) -> str:
    """Generate a random numeric code for SMS verification."""
    return "".join(secrets.choice("0123456789") for _ in range(length))


def hash_code(code: str) -> str:
    """Hash a verification code for storage. Uses HMAC-SHA256 with SESSION_SECRET."""
    return hmac.new(
        settings.SESSION_SECRET.encode("utf-8"),
        code.encode("utf-8"),
        hashlib.sha256,
    ).hexdigest()


def verify_code(code: str, stored_hash: str) -> bool:
    """Verify a code against a stored hash. Constant-time comparison."""
    computed = hash_code(code)
    return hmac.compare_digest(computed, stored_hash)
