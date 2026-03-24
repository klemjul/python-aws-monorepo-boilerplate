"""AWS Lambda handler for the Hello endpoint."""

import json
import os
import uuid
from typing import Any

import boto3
from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def _handle_get(event: dict[str, Any]) -> dict[str, Any]:
    query_params = event.get("queryStringParameters") or {}
    name = query_params.get("name") or "World"
    return build_response(200, {"message": f"Hello, {name}!"})


def _handle_post(event: dict[str, Any]) -> dict[str, Any]:
    body: dict[str, Any] = json.loads(event.get("body") or "{}")
    name = body.get("name") or "World"
    item_id = str(uuid.uuid4())
    message = f"Hello, {name}!"
    table = boto3.resource("dynamodb").Table(os.environ["GREETINGS_TABLE"])
    table.put_item(Item={"id": item_id, "name": name, "message": message})
    return build_response(201, {"id": item_id, "message": message})


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point — routes GET and POST requests for the /hello endpoint."""
    method = (event.get("httpMethod") or "GET").upper()
    if method == "POST":
        return _handle_post(event)
    return _handle_get(event)
