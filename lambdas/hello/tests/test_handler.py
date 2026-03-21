"""Tests for the hello Lambda handler."""

import json
from typing import Any

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from hello.handler import handler


def _apigw_event(query_params: dict[str, str] | None = None) -> dict[str, Any]:
    """Build a minimal API Gateway proxy event for the /hello GET route."""
    return {
        "httpMethod": "GET",
        "path": "/hello",
        "queryStringParameters": query_params,
        "headers": {},
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {
            "resourcePath": "/hello",
            "httpMethod": "GET",
        },
    }


@pytest.fixture
def context() -> LambdaContext:
    ctx = LambdaContext()
    ctx._function_name = "hello"
    ctx._memory_limit_in_mb = 128
    ctx._aws_request_id = "test-request-id"
    return ctx


def test_handler_default_name(context: LambdaContext) -> None:
    result = handler(_apigw_event(), context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_with_name(context: LambdaContext) -> None:
    result = handler(_apigw_event({"name": "Alice"}), context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, Alice!"}


def test_handler_empty_query_params(context: LambdaContext) -> None:
    result = handler(_apigw_event({}), context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_none_query_params(context: LambdaContext) -> None:
    result = handler(_apigw_event(None), context)
    assert result["statusCode"] == 200
    assert json.loads(result["body"]) == {"message": "Hello, World!"}


def test_handler_response_has_content_type(context: LambdaContext) -> None:
    result = handler(_apigw_event(), context)
    assert "application/json" in result["multiValueHeaders"]["Content-Type"]


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_handler_various_names(name: str, context: LambdaContext) -> None:
    result = handler(_apigw_event({"name": name}), context)
    assert json.loads(result["body"]) == {"message": f"Hello, {name}!"}
