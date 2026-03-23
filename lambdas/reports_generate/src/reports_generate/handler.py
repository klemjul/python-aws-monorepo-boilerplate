"""AWS Lambda handler for the Generate Report endpoint."""

from typing import Any

from aws_lambda_powertools.utilities.typing import LambdaContext
from shared.aws.apigw.response import build_response


def handler(event: dict[str, Any], context: LambdaContext) -> dict[str, Any]:
    """Lambda entry point starts report generation."""
    return build_response(
        202, {"message": "Report generation started", "reportId": "report-1"}
    )
