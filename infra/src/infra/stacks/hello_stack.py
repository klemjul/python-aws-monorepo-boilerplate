"""AWS CDK stack for the Hello API Gateway + Lambda + Layer deployment."""

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
    gitignore_exclude_patterns,
)

LAMBDA_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")


class HelloStack(cdk.Stack):
    """Stack that deploys the Hello Lambda behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        hello_fn = self._create_hello_function()

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

    def _create_hello_function(self) -> lambda_.Function:
        """Create the Hello Lambda function with its dependencies layer."""
        # HelloDepsLayer: install only the runtime deps.
        # The asset hash is derived from pyproject.toml so the layer is only
        # rebuilt when the dependency changes.
        hello_deps_layer = lambda_.LayerVersion(
            self,
            "HelloDepsLayer",
            code=lambda_.Code.from_asset(
                LAMBDA_DIR,
                asset_hash_type=cdk.AssetHashType.CUSTOM,
                asset_hash=deps_hash(LAMBDA_DIR),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=cast(cdk.ILocalBundling, DepsBundler(LAMBDA_DIR)),
                    # Docker fallback is intentionally disabled: DepsBundler
                    # raises RuntimeError when uv is not available, so CDK
                    # will never reach the Docker path.
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

        return lambda_.Function(
            self,
            "HelloFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="hello.handler.handler",
            code=lambda_.Code.from_asset(
                os.path.join(LAMBDA_DIR, "src"),
                exclude=gitignore_exclude_patterns(),
                ignore_mode=cdk.IgnoreMode.GIT,
            ),
            layers=[hello_deps_layer],
            timeout=cdk.Duration.seconds(30),
            memory_size=256,
            environment={
                "LOG_LEVEL": "INFO",
            },
            description="Hello World Lambda function",
        )
