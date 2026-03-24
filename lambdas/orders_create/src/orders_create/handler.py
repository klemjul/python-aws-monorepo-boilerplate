"""AWS Lambda handler for the Create Order endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point creates an order."""
    return build_response(201, {"message": "Order created", "id": "order-1"})
