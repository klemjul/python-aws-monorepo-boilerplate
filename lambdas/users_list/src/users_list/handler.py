"""AWS Lambda handler for the List Users endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point lists all users."""
    return build_response(200, {"users": [], "total": 0})
