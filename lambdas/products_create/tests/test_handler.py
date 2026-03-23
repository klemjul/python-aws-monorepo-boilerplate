"""Tests for the products_create Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from products_create.handler import handler


def _apigw_event(body: str | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "POST",
        "path": "/products",
        "queryStringParameters": None,
        "headers": {},
        "body": body,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_create_product_returns_201(context: LambdaContext) -> None:
    result = handler(_apigw_event('{"name": "Widget"}'), context)
    assert result["statusCode"] == 201
    body = json.loads(result["body"])
    assert body["message"] == "Product created"
