"""Tests for the hello Lambda handler."""

import json

import pytest
from hello.handler import handler


class FakeContext:
    """Minimal mock of the AWS Lambda context object."""

    function_name = "hello"
    memory_limit_in_mb = 128
    aws_request_id = "test-request-id"


@pytest.fixture
def context() -> FakeContext:
    return FakeContext()


def test_handler_default_name(context: FakeContext) -> None:
    event: dict[str, object] = {}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_with_name(context: FakeContext) -> None:
    event: dict[str, object] = {"queryStringParameters": {"name": "Alice"}}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, Alice!"}


def test_handler_empty_query_params(context: FakeContext) -> None:
    event: dict[str, object] = {"queryStringParameters": {}}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_none_query_params(context: FakeContext) -> None:
    event: dict[str, object] = {"queryStringParameters": None}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_response_has_content_type(context: FakeContext) -> None:
    event: dict[str, object] = {}
    result = handler(event, context)
    assert result["headers"]["Content-Type"] == "application/json"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_handler_various_names(name: str, context: FakeContext) -> None:
    event: dict[str, object] = {"queryStringParameters": {"name": name}}
    result = handler(event, context)
    assert json.loads(result["body"]) == {"message": f"Hello, {name}!"}
