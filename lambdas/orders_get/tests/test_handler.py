"""Tests for the orders_get Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from orders_get.handler import handler


def _apigw_event(path_params: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "GET",
        "path": "/orders/{id}",
        "queryStringParameters": None,
        "headers": {},
        "body": None,
        "pathParameters": path_params,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_get_order_returns_200_with_status(context: LambdaContext) -> None:
    result = handler(_apigw_event({"id": "order-10"}), context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["id"] == "order-10"
    assert body["status"] == "pending"
