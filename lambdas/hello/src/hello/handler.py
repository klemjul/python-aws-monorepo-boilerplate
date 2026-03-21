"""AWS Lambda handler for the Hello endpoint."""

from typing import Any

from aws_lambda_powertools.event_handler import APIGatewayRestResolver
from aws_lambda_powertools.utilities.typing import LambdaContext

app = APIGatewayRestResolver()


@app.get("/hello")
def get_hello() -> dict[str, Any]:
    """Handle GET /hello and return a greeting response."""
    name = app.current_event.get_query_string_value("name") or "World"
    return {"message": f"Hello, {name}!"}


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point — resolves the API Gateway event via Powertools router."""
    return app.resolve(event, context)
