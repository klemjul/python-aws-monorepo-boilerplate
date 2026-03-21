"""Tests for the shared response module."""

import json

import pytest
from shared.response import build_response


def test_build_response_default_headers() -> None:
    result = build_response(200, {"message": "ok"})
    assert result["statusCode"] == 200
    assert result["headers"]["Content-Type"] == "application/json"
    assert json.loads(result["body"]) == {"message": "ok"}


def test_build_response_custom_headers() -> None:
    result = build_response(200, {"message": "ok"}, {"X-Custom": "value"})
    assert result["headers"]["X-Custom"] == "value"
    assert result["headers"]["Content-Type"] == "application/json"


def test_build_response_error_status() -> None:
    result = build_response(500, {"error": "internal server error"})
    assert result["statusCode"] == 500
    assert json.loads(result["body"]) == {"error": "internal server error"}


def test_build_response_body_is_json_string() -> None:
    result = build_response(201, {"id": "abc123"})
    assert isinstance(result["body"], str)
    assert json.loads(result["body"])["id"] == "abc123"


@pytest.mark.parametrize(
    ("status_code", "body"),
    [
        (200, {"key": "value"}),
        (400, {"error": "bad request"}),
        (404, {"error": "not found"}),
    ],
)
def test_build_response_various_status_codes(
    status_code: int, body: dict[str, str]
) -> None:
    result = build_response(status_code, body)
    assert result["statusCode"] == status_code
    assert json.loads(result["body"]) == body
