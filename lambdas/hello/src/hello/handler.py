"""AWS Lambda handler for the Hello endpoint."""

from typing import Any

from shared.response import build_response


def handler(event: dict[str, Any], context: object) -> dict[str, Any]:
    """Handle API Gateway proxy event and return a greeting response.

    Args:
        event: The API Gateway Lambda Proxy event dict.
        context: The Lambda runtime context object.

    Returns:
        An API Gateway Lambda Proxy response with a greeting message.
    """
    name = _get_name(event)
    return build_response(200, {"message": f"Hello, {name}!"})


def _get_name(event: dict[str, Any]) -> str:
    """Extract the name query string parameter from the event.

    Args:
        event: The API Gateway Lambda Proxy event dict.

    Returns:
        The name from query string parameters, or "World" if not provided.
    """
    query_params: dict[str, str] | None = event.get("queryStringParameters")
    if query_params:
        return str(query_params.get("name", "World"))
    return "World"
