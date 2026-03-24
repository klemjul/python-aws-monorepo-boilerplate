"""Authentication token utilities.

.. warning::
    These utilities are **structural helpers only** and are **not suitable for
    production authentication**:

    * ``verify_token`` / ``decode_token`` perform base64/JSON structural checks
      with **no cryptographic signature verification** — tokens can be trivially
      forged.  Use a proper JWT library (e.g. ``python-jose``, ``PyJWT``) with
      signature verification for real auth decisions.
    * ``hash_password`` uses PBKDF2-HMAC-SHA256 with a random salt — this is
      suitable for development/demo use.  For production, prefer ``argon2`` or
      ``bcrypt`` which offer stronger memory-hard guarantees.
"""

import base64
import hashlib
import hmac
import json
import os
from typing import Any

_PBKDF2_ITERATIONS = 260_000


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
    """Hash a password using PBKDF2-HMAC-SHA256 with a random salt.

    Returns a base64-encoded string that encodes the 16-byte salt followed
    by the 32-byte derived key.  Use :func:`verify_password` to check a
    plain-text password against the stored hash.

    Args:
        password: The plain-text password to hash.

    Returns:
        A base64-encoded string containing the salt and derived key.
    """
    salt = os.urandom(16)
    dk = hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
    )
    return base64.b64encode(salt + dk).decode("ascii")


def verify_password(password: str, hashed: str) -> bool:
    """Verify a plain-text password against a stored hash.

    Args:
        password: The plain-text password to check.
        hashed: A hash previously produced by :func:`hash_password`.

    Returns:
        True if the password matches, False otherwise.
    """
    try:
        raw = base64.b64decode(hashed)
        salt = raw[:16]
        stored_dk = raw[16:]
        dk = hashlib.pbkdf2_hmac(
            "sha256", password.encode("utf-8"), salt, _PBKDF2_ITERATIONS
        )
        return hmac.compare_digest(dk, stored_dk)
    except Exception:
        return False
