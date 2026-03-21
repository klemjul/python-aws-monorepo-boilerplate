"""Tests for the hello Lambda handler."""

import json
from typing import Any

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from hello.handler import handler


@pytest.fixture
def context() -> LambdaContext:
    ctx = LambdaContext()
    ctx._function_name = "hello"
    ctx._memory_limit_in_mb = 128
    ctx._aws_request_id = "test-request-id"
    return ctx


def test_handler_default_name(context: LambdaContext) -> None:
    event: dict[str, Any] = {}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_with_name(context: LambdaContext) -> None:
    event: dict[str, Any] = {"queryStringParameters": {"name": "Alice"}}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, Alice!"}


def test_handler_empty_query_params(context: LambdaContext) -> None:
    event: dict[str, Any] = {"queryStringParameters": {}}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_none_query_params(context: LambdaContext) -> None:
    event: dict[str, Any] = {"queryStringParameters": None}
    result = handler(event, context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_response_has_content_type(context: LambdaContext) -> None:
    event: dict[str, Any] = {}
    result = handler(event, context)
    assert result["headers"]["Content-Type"] == "application/json"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_handler_various_names(name: str, context: LambdaContext) -> None:
    event: dict[str, Any] = {"queryStringParameters": {"name": name}}
    result = handler(event, context)
    assert json.loads(result["body"]) == {"message": f"Hello, {name}!"}
