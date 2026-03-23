"""Tests for the orders_update Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from orders_update.handler import handler


def _apigw_event(path_params: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "PUT",
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


def test_update_order_returns_200(context: LambdaContext) -> None:
    result = handler(_apigw_event({"id": "order-20"}), context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Order updated"
    assert body["id"] == "order-20"
