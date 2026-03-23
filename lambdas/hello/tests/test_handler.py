"""Tests for the hello Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

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
    return MagicMock(spec=LambdaContext)


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
    assert result["headers"]["Content-Type"] == "application/json"


@pytest.mark.parametrize("name", ["Bob", "Charlie", "Django"])
def test_handler_various_names(name: str, context: LambdaContext) -> None:
    result = handler(_apigw_event({"name": name}), context)
    assert json.loads(result["body"]) == {"message": f"Hello, {name}!"}
