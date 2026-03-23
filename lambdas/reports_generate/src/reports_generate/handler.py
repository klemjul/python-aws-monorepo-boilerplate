"""AWS Lambda handler for the Generate Report endpoint."""

from typing import Any
from uuid import uuid4

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point starts report generation."""
    report_id = f"report-{uuid4().hex}"
    return build_response(
        202, {"message": "Report generation started", "reportId": report_id}
    )
