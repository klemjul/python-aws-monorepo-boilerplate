"""Integration tests for the hello Lambda handler.

These tests use moto to mock the AWS environment and verify:
1. The Lambda function can be registered with the expected deployment configuration.
2. The handler produces correct API Gateway responses when invoked inside the
   mocked AWS context (environment variables, IAM, etc. all wired up by moto).
"""

import io
import json
import zipfile
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import boto3
import pytest
from aws_lambda_powertools.utilities.typing import LambdaContext
from moto import mock_aws

from hello.handler import handler

_REGION = "us-east-1"
_FUNCTION_NAME = "hello"
_HANDLER = "hello.handler.handler"
_RUNTIME = "python3.13"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _build_lambda_zip() -> bytes:
    """Bundle the hello handler and the shared dependency into a deployment zip."""
    buf = io.BytesIO()
    repo_root = Path(__file__).parents[4]
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        hello_src = repo_root / "lambdas" / "hello" / "src"
        for p in hello_src.rglob("*.py"):
            zf.write(p, p.relative_to(hello_src))
        shared_src = repo_root / "packages" / "shared" / "src"
        for p in shared_src.rglob("*.py"):
            zf.write(p, p.relative_to(shared_src))
    return buf.getvalue()


def _apigw_event(query_params: dict[str, str] | None = None) -> dict[str, Any]:
    """Return a minimal API Gateway proxy event."""
    return {
        "httpMethod": "GET",
        "path": "/hello",
        "queryStringParameters": query_params,
        "headers": {},
        "body": None,
        "isBase64Encoded": False,
        "requestContext": {"resourcePath": "/hello", "httpMethod": "GET"},
    }


@pytest.fixture
def lambda_context() -> LambdaContext:
    return MagicMock(spec=LambdaContext)


# ---------------------------------------------------------------------------
# Deployment smoke tests — validate the AWS resource configuration via SDK
# ---------------------------------------------------------------------------


class TestHelloLambdaDeployment:
    """Verify that the Lambda function can be registered correctly in AWS."""

    @mock_aws
    def test_function_is_created_successfully(self) -> None:
        iam = boto3.client("iam", region_name=_REGION)
        role_arn = iam.create_role(
            RoleName="hello-lambda-role",
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
        )["Role"]["Arn"]

        client = boto3.client("lambda", region_name=_REGION)
        response = client.create_function(
            FunctionName=_FUNCTION_NAME,
            Runtime=_RUNTIME,
            Role=role_arn,
            Handler=_HANDLER,
            Code={"ZipFile": _build_lambda_zip()},
        )

        assert response["FunctionName"] == _FUNCTION_NAME
        assert response["Runtime"] == _RUNTIME
        assert response["Handler"] == _HANDLER

    @mock_aws
    def test_function_is_listed_after_creation(self) -> None:
        iam = boto3.client("iam", region_name=_REGION)
        role_arn = iam.create_role(
            RoleName="hello-lambda-role",
            AssumeRolePolicyDocument=json.dumps(
                {
                    "Version": "2012-10-17",
                    "Statement": [
                        {
                            "Effect": "Allow",
                            "Principal": {"Service": "lambda.amazonaws.com"},
                            "Action": "sts:AssumeRole",
                        }
                    ],
                }
            ),
        )["Role"]["Arn"]

        client = boto3.client("lambda", region_name=_REGION)
        client.create_function(
            FunctionName=_FUNCTION_NAME,
            Runtime=_RUNTIME,
            Role=role_arn,
            Handler=_HANDLER,
            Code={"ZipFile": _build_lambda_zip()},
        )

        functions = client.list_functions()["Functions"]
        names = [f["FunctionName"] for f in functions]
        assert _FUNCTION_NAME in names


# ---------------------------------------------------------------------------
# Handler behaviour tests — invoke the handler inside the mocked AWS context
# ---------------------------------------------------------------------------


class TestHelloLambdaHandler:
    """Invoke the handler directly within a mocked AWS environment."""

    @mock_aws
    def test_default_greeting(self, lambda_context: LambdaContext) -> None:
        result = handler(_apigw_event(), lambda_context)
        assert result["statusCode"] == 200
        assert json.loads(result["body"]) == {"message": "Hello, World!"}

    @mock_aws
    def test_custom_name_from_query_param(self, lambda_context: LambdaContext) -> None:
        result = handler(_apigw_event({"name": "Alice"}), lambda_context)
        assert result["statusCode"] == 200
        assert json.loads(result["body"]) == {"message": "Hello, Alice!"}

    @mock_aws
    def test_response_content_type_header(self, lambda_context: LambdaContext) -> None:
        result = handler(_apigw_event(), lambda_context)
        assert result["headers"]["Content-Type"] == "application/json"
