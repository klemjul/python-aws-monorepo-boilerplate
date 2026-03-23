"""AWS CDK stack for the Reports API Gateway + Lambda + Layer deployment."""

import os
from typing import Any, cast

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from infra.utils.bundler import (
    REPO_ROOT,
    DepsBundler,
    deps_hash,
)


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

        reports_generate_fn = self._create_function(
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

    def _create_function(
        self,
        logical_id: str,
        lambda_dir: str,
        handler: str,
        description: str,
    ) -> lambda_.Function:
        """Create a Lambda function with its dependency layer."""
        layer = lambda_.LayerVersion(
            self,
            f"{logical_id}DepsLayer",
            code=lambda_.Code.from_asset(
                lambda_dir,
                asset_hash_type=cdk.AssetHashType.CUSTOM,
                asset_hash=deps_hash(lambda_dir),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=cast(cdk.ILocalBundling, DepsBundler(lambda_dir)),
                    command=[
                        "bash",
                        "-c",
                        (
                            "echo 'Error: Docker bundling is disabled;"
                            " install uv to use local bundling.' >&2; exit 1"
                        ),
                    ],
                ),
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            description=f"{description} dependencies",
        )

        return lambda_.Function(
            self,
            f"{logical_id}Function",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler=handler,
            code=lambda_.Code.from_asset(
                os.path.join(lambda_dir, "src"),
            ),
            layers=[layer],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment={
                "LOG_LEVEL": "INFO",
            },
            description=description,
        )
