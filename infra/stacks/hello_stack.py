"""AWS CDK stack for the Hello API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
from constructs import Construct
from utils.bundler import REPO_ROOT, DepsBundler

LAMBDA_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")


class HelloStack(cdk.Stack):
    """Stack that deploys the Hello Lambda behind an API Gateway REST API.

    Architecture:
    - HelloDepsLayer: Lambda Layer with all runtime deps from
      lambdas/hello/pyproject.toml (shared + any third-party packages).
    - HelloFunction: Lambda function containing only the handler source code.
    - API Gateway REST API routing GET /hello to the Lambda.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # HelloDepsLayer: install all runtime deps declared in
        # lambdas/hello/pyproject.toml into the layer.  The asset source is
        # LAMBDA_DIR so the layer hash tracks changes to pyproject.toml.
        # The local bundler installs from LAMBDA_DIR with uv, which resolves
        # workspace sources (e.g. 'shared') automatically.
        hello_deps_layer = lambda_.LayerVersion(
            self,
            "HelloDepsLayer",
            code=lambda_.Code.from_asset(
                LAMBDA_DIR,
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=DepsBundler(LAMBDA_DIR),  # type: ignore[arg-type]  # jsii protocol vs mypy stub mismatch
                    # Docker fallback is intentionally disabled: the Docker
                    # context (/asset-input) only contains the lambda directory,
                    # so pip cannot resolve workspace dependencies (e.g. `shared`)
                    # declared via [tool.uv.sources].  Install uv locally to use
                    # the faster and correct local bundling path instead.
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
            description="Hello Lambda runtime dependencies",
        )

        # Lambda function: only the handler source — all imports resolved by the layer
        hello_fn = lambda_.Function(
            self,
            "HelloFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="hello.handler.handler",
            code=lambda_.Code.from_asset(
                os.path.join(LAMBDA_DIR, "src"),
            ),
            layers=[hello_deps_layer],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment={
                "LOG_LEVEL": "INFO",
            },
            description="Hello World Lambda function",
        )

        # API Gateway
        api = apigw.RestApi(
            self,
            "HelloApi",
            rest_api_name="hello-api",
            description="API Gateway for Hello Lambda",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        hello_integration = apigw.LambdaIntegration(hello_fn)
        hello_resource = api.root.add_resource("hello")
        hello_resource.add_method("GET", hello_integration)

        cdk.CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway URL")
