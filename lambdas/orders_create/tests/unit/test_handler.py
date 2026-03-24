"""Tests for the orders_create Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from orders_create.handler import handler


def _apigw_event(body: str | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "POST",
        "path": "/orders",
        "queryStringParameters": None,
        "headers": {},
        "body": body,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_create_order_returns_201(context: LambdaContext) -> None:
    result = handler(_apigw_event('{"item": "widget"}'), context)
    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["message"] == "Order created"
