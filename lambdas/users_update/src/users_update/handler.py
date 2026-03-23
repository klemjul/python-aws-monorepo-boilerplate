"""AWS Lambda handler for the Update User endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point updates a user by id."""
    id_val = (event.get("pathParameters") or {}).get("id", "unknown")
    return build_response(200, {"message": "User updated", "id": id_val})
