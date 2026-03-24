"""Tests for the products_list Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from products_list.handler import handler


def _apigw_event() -> dict[str, Any]:
    return {
        "httpMethod": "GET",
        "path": "/products",
        "queryStringParameters": None,
        "headers": {},
        "body": None,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_list_products_returns_200(context: LambdaContext) -> None:
    result = handler(_apigw_event(), context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert "products" in body
    assert body["total"] == 0
