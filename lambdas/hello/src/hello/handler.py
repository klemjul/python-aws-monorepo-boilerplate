"""AWS Lambda handler for the Hello endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.data_classes import APIGatewayProxyEvent
from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Handle API Gateway proxy event and return a greeting response.

    Args:
        event: The raw API Gateway Lambda Proxy event dict.
        context: The Lambda runtime context.

    Returns:
        An API Gateway Lambda Proxy response with a greeting message.
    """
    proxy_event = APIGatewayProxyEvent(event)
    params = proxy_event.query_string_parameters
    name = params.get("name", "World") if params else "World"
    return build_response(200, {"message": f"Hello, {name}!"})
