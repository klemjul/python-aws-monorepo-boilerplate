"""AWS Lambda handler for the Get Product endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point retrieves a product by id."""
    id_val = (event.get("pathParameters") or {}).get("id", "unknown")
    return build_response(200, {"id": id_val, "name": "Product"})
