"""AWS CDK stack for the Hello API Gateway + Lambda + Layer deployment."""

import hashlib
import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from infra.utils.bundler import REPO_ROOT, DepsBundler

LAMBDA_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")


def _deps_hash(lambda_dir: str) -> str:
    """Compute a hash from the lambda's ``pyproject.toml`` only.

    The layer is rebuilt only when ``pyproject.toml`` changes, not when the
    handler source code changes.
    """
    hasher = hashlib.sha256()
    filepath = os.path.join(lambda_dir, "pyproject.toml")
    if os.path.exists(filepath):
        with open(filepath, "rb") as f:
            hasher.update(f.read())
    return hasher.hexdigest()[:32]


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

        # HelloDepsLayer: install only the runtime deps declared in
        # lambdas/hello/pyproject.toml into the layer (not the hello package
        # itself — that is deployed separately via Code.from_asset).
        # The asset hash is derived from pyproject.toml so the layer is only
        # rebuilt when the dependency manifest changes, not on every handler
        # code edit.
        hello_deps_layer = lambda_.LayerVersion(
            self,
            "HelloDepsLayer",
            code=lambda_.Code.from_asset(
                LAMBDA_DIR,
                asset_hash_type=cdk.AssetHashType.CUSTOM,
                asset_hash=_deps_hash(LAMBDA_DIR),
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=DepsBundler(LAMBDA_DIR),  # type: ignore[arg-type]  # jsii protocol vs mypy stub mismatch
                    # Docker fallback is intentionally disabled: DepsBundler
                    # raises RuntimeError when uv is not available, so CDK
                    # will never reach the Docker path.  Install uv locally
                    # to use the correct local bundling path.
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
