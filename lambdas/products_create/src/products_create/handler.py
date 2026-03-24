"""AWS Lambda handler for the Create Product endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point creates a product."""
    return build_response(201, {"message": "Product created", "id": "product-1"})
