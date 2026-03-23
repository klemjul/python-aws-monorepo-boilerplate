"""Tests for auth.token utilities."""

import base64
import json

import pytest
from auth.token import decode_token, hash_password, verify_token


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
# hash_password
# ---------------------------------------------------------------------------


def test_hash_password_returns_hex_string() -> None:
    result = hash_password("secret")
    assert isinstance(result, str)
    assert len(result) == 64  # SHA-256 produces 32 bytes = 64 hex chars


def test_hash_password_same_input_same_output() -> None:
    assert hash_password("password") == hash_password("password")


def test_hash_password_different_inputs_different_outputs() -> None:
    assert hash_password("abc") != hash_password("xyz")
