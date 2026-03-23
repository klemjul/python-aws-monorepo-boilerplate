"""Authentication token utilities.

.. warning::
    These utilities are **structural helpers only** and are **not suitable for
    production authentication**:

    * ``verify_token`` / ``decode_token`` perform base64/JSON structural checks
      with **no cryptographic signature verification** — tokens can be trivially
      forged.  Use a proper JWT library (e.g. ``python-jose``, ``PyJWT``) with
      signature verification for real auth decisions.
    * ``hash_password`` uses plain SHA-256 with **no salt or key-stretching** —
      it is vulnerable to rainbow-table attacks.  Use ``bcrypt``, ``argon2``,
      or ``scrypt`` in production.
"""

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
        return dict(json.loads(decoded))
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
