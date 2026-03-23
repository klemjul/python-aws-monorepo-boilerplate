"""HTTP response helpers for AWS API Gateway Lambda Proxy integration."""

import json
from typing import Any


def build_response(
    status_code: int,
    body: dict[str, Any],
    headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Build an API Gateway Lambda Proxy response dict.

    Args:
        status_code: HTTP status code (e.g. 200, 400, 500).
        body: Response payload to be JSON-encoded.
        headers: Optional extra HTTP headers to include.

    Returns:
        A dict conforming to the API Gateway Lambda Proxy response format.
    """
    default_headers: dict[str, str] = {"Content-Type": "application/json"}
    if headers:
        default_headers.update(headers)
    return {
        "statusCode": status_code,
        "headers": default_headers,
        "body": json.dumps(body),
    }
