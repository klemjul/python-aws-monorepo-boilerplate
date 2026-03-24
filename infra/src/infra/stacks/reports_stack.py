"""AWS CDK stack for the Reports API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function


class ReportsStack(cdk.Stack):
    """Stack that deploys the Reports Lambda behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            "ReportsApi",
            rest_api_name="reports-api",
            description="API Gateway for Reports Lambdas",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        reports_generate_fn = create_lambda_function(
            self,
            "ReportsGenerate",
            os.path.join(REPO_ROOT, "lambdas", "reports_generate"),
            "reports_generate.handler.handler",
            "Generate Report Lambda function",
        )

        reports_resource = api.root.add_resource("reports")
        generate_resource = reports_resource.add_resource("generate")
        generate_resource.add_method(
            "POST", apigw.LambdaIntegration(reports_generate_fn)
        )

        cdk.CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway URL")
