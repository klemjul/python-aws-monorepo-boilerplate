"""AWS Lambda handler for the Hello endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point returns a greeting using the shared build_response helper."""
    query_params = event.get("queryStringParameters") or {}
    name = query_params.get("name") or "World"
    return build_response(200, {"message": f"Hello, {name}!"})
