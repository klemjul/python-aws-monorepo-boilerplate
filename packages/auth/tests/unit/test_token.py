"""Tests for auth.token utilities."""

import base64
import json

import pytest
from auth.token import decode_token, hash_password, verify_password, verify_token


def _make_token(payload: dict) -> str:
    """Encode a dict as a base64 token (padding stripped for realism)."""
    raw = json.dumps(payload).encode("utf-8")
    return base64.b64encode(raw).decode("utf-8").rstrip("=")


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------


def test_verify_token_valid() -> None:
    token = _make_token({"sub": "user-123", "role": "admin"})
    assert verify_token(token) is True


def test_verify_token_missing_sub() -> None:
    token = _make_token({"role": "admin"})
    assert verify_token(token) is False


def test_verify_token_empty_string() -> None:
    assert verify_token("") is False


def test_verify_token_invalid_base64() -> None:
    assert verify_token("not-valid-base64!!!") is False


def test_verify_token_non_dict_payload() -> None:
    raw = base64.b64encode(b"[1, 2, 3]").decode()
    assert verify_token(raw) is False


# ---------------------------------------------------------------------------
# decode_token
# ---------------------------------------------------------------------------


def test_decode_token_returns_claims() -> None:
    payload = {"sub": "user-123", "role": "viewer"}
    token = _make_token(payload)
    claims = decode_token(token)
    assert claims["sub"] == "user-123"
    assert claims["role"] == "viewer"


def test_decode_token_raises_on_invalid_token() -> None:
    with pytest.raises(ValueError, match="Invalid token"):
        decode_token("!!!invalid!!!")


# ---------------------------------------------------------------------------
# hash_password / verify_password
# ---------------------------------------------------------------------------


def test_hash_password_returns_string() -> None:
    result = hash_password("secret")
    assert isinstance(result, str)
    assert len(result) > 0


def test_hash_password_output_is_base64() -> None:
    result = hash_password("secret")
    # Must be valid base64 and decode to at least 48 bytes (16 salt + 32 dk)
    raw = base64.b64decode(result)
    assert len(raw) == 48


def test_hash_password_unique_per_call() -> None:
    """Each call produces a different hash due to the random salt."""
    assert hash_password("password") != hash_password("password")


def test_hash_password_different_inputs_different_outputs() -> None:
    h1 = hash_password("abc")
    h2 = hash_password("xyz")
    assert h1 != h2


def test_verify_password_correct_password() -> None:
    hashed = hash_password("my-secret")
    assert verify_password("my-secret", hashed) is True


def test_verify_password_wrong_password() -> None:
    hashed = hash_password("my-secret")
    assert verify_password("wrong-password", hashed) is False


def test_verify_password_invalid_hash() -> None:
    assert verify_password("password", "not-valid-base64!!!") is False
