"""Tests for the products_update Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from products_update.handler import handler


def _apigw_event(path_params: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "PUT",
        "path": "/products/{id}",
        "queryStringParameters": None,
        "headers": {},
        "body": None,
        "pathParameters": path_params,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_update_product_returns_200(context: LambdaContext) -> None:
    result = handler(_apigw_event({"id": "product-3"}), context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Product updated"
    assert body["id"] == "product-3"
