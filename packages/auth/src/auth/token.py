"""Authentication token utilities."""

import base64
import hashlib
import json
from typing import Any


def verify_token(token: str) -> bool:
    """Verify that a bearer token has the expected structure.

    This is a lightweight structural check only — it does not perform
    cryptographic signature verification.

    Args:
        token: A base64-encoded JSON token string.

    Returns:
        True if the token is structurally valid, False otherwise.
    """
    if not token:
        return False
    try:
        decoded = base64.b64decode(token + "==").decode("utf-8")
        payload = json.loads(decoded)
        return isinstance(payload, dict) and "sub" in payload
    except Exception:
        return False


def decode_token(token: str) -> dict[str, Any]:
    """Decode a bearer token and return its claims.

    Args:
        token: A base64-encoded JSON token string.

    Returns:
        A dict of token claims.

    Raises:
        ValueError: If the token cannot be decoded.
    """
    try:
        decoded = base64.b64decode(token + "==").decode("utf-8")
        return dict(json.loads(decoded))  # type: ignore[arg-type]
    except Exception as exc:
        raise ValueError(f"Invalid token: {exc}") from exc


def hash_password(password: str) -> str:
    """Return a SHA-256 hex digest of the given password.

    This is intentionally simple — use a proper KDF in production.

    Args:
        password: The plain-text password to hash.

    Returns:
        A hex-encoded SHA-256 digest string.
    """
    return hashlib.sha256(password.encode()).hexdigest()
