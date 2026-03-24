"""Tests for the reports_generate Lambda handler."""

import json
from typing import Any
from unittest.mock import MagicMock

import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from reports_generate.handler import handler


def _apigw_event() -> dict[str, Any]:
    return {
        "httpMethod": "POST",
        "path": "/reports/generate",
        "queryStringParameters": None,
        "headers": {},
        "body": None,
        "isBase64Encoded": False,
    }


@pytest.fixture
def context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


def test_generate_report_returns_202(context: LambdaContext) -> None:
    result = handler(_apigw_event(), context)
    assert result["statusCode"] == 202
    body = json.loads(result["body"])
    assert body["message"] == "Report generation started"
    assert isinstance(body["reportId"], str) and body["reportId"].startswith("report-")


def test_generate_report_unique_report_id(context: LambdaContext) -> None:
    result_a = handler(_apigw_event(), context)
    result_b = handler(_apigw_event(), context)
    id_a = json.loads(result_a["body"])["reportId"]
    id_b = json.loads(result_b["body"])["reportId"]
    assert id_a != id_b
