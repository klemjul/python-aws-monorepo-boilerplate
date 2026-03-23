"""Tests for the products_delete Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from products_delete.handler import handler


def _apigw_event(path_params: dict[str, str] | None = None) -> dict[str, Any]:
    return {
        "httpMethod": "DELETE",
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


def test_delete_product_returns_200(context: LambdaContext) -> None:
    result = handler(_apigw_event({"id": "product-5"}), context)
    assert result["statusCode"] == 200
    body = json.loads(result["body"])
    assert body["message"] == "Product deleted"
    assert body["id"] == "product-5"


def test_delete_product_returns_400_when_id_missing(context: LambdaContext) -> None:
    result = handler(_apigw_event(None), context)
    assert result["statusCode"] == 400
    body = json.loads(result["body"])
    assert "id" in body["message"].lower()
