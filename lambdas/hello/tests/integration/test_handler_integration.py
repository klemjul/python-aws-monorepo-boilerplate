"""Integration tests for the hello Lambda handler.

These tests use moto to mock DynamoDB and verify that the POST /hello route
correctly writes a greeting item to the table and returns the expected response.
"""

import json
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from hello.handler import handler
from moto import mock_aws

_REGION = "us-east-1"
_TABLE_NAME = "greetings"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _post_event(name: str | None = None) -> dict[str, Any]:
    """Return a minimal API Gateway proxy event for POST /hello."""
    body = json.dumps({"name": name}) if name is not None else None
    return {
        "httpMethod": "POST",
        "path": "/hello",
        "queryStringParameters": None,
        "headers": {"Content-Type": "application/json"},
        "body": body,
        "isBase64Encoded": False,
        "requestContext": {"resourcePath": "/hello", "httpMethod": "POST"},
    }


@pytest.fixture
def lambda_context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


@pytest.fixture
def greetings_table(monkeypatch: pytest.MonkeyPatch) -> Any:
    """Create a mocked DynamoDB table and set the required env vars."""
    with mock_aws():
        monkeypatch.setenv("GREETINGS_TABLE", _TABLE_NAME)
        monkeypatch.setenv("AWS_DEFAULT_REGION", _REGION)
        dynamodb = boto3.resource("dynamodb", region_name=_REGION)
        table = dynamodb.create_table(
            TableName=_TABLE_NAME,
            KeySchema=[{"AttributeName": "id", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "id", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )
        yield table


# ---------------------------------------------------------------------------
# POST /hello — writes a greeting to DynamoDB
# ---------------------------------------------------------------------------


class TestHelloLambdaPostRoute:
    """Verify that POST /hello writes to DynamoDB and returns the item id."""

    def test_post_writes_item_to_table(
        self, greetings_table: Any, lambda_context: LambdaContext
    ) -> None:
        result = handler(_post_event("Alice"), lambda_context)

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["message"] == "Hello, Alice!"
        assert "id" in body

        stored = greetings_table.get_item(Key={"id": body["id"]})["Item"]
        assert stored["name"] == "Alice"
        assert stored["message"] == "Hello, Alice!"

    def test_post_without_name_uses_world(
        self, greetings_table: Any, lambda_context: LambdaContext
    ) -> None:
        result = handler(_post_event(), lambda_context)

        assert result["statusCode"] == 201
        body = json.loads(result["body"])
        assert body["message"] == "Hello, World!"

        stored = greetings_table.get_item(Key={"id": body["id"]})["Item"]
        assert stored["name"] == "World"

    def test_post_each_call_stores_distinct_item(
        self, greetings_table: Any, lambda_context: LambdaContext
    ) -> None:
        r1 = handler(_post_event("Bob"), lambda_context)
        r2 = handler(_post_event("Charlie"), lambda_context)

        id1 = json.loads(r1["body"])["id"]
        id2 = json.loads(r2["body"])["id"]
        assert id1 != id2

        items = greetings_table.scan()["Items"]
        assert len(items) == 2
