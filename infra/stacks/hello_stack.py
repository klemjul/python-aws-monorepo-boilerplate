"""AWS CDK stack for the Hello API Gateway + Lambda + Layer deployment."""

import os
import shutil
import subprocess
import sys
from typing import Any

import aws_cdk as cdk
import jsii
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

LAMBDA_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "lambdas", "hello")
SHARED_DIR = os.path.join(os.path.dirname(__file__), "..", "..", "packages", "shared")


@jsii.implements(cdk.ILocalBundling)
class PipLocalBundler:
    """Local bundler that installs a Python package with pip.

    Used as a fallback when Docker is not available (e.g. in CI synth).
    """

    def __init__(self, source_dir: str) -> None:
        self._source_dir = source_dir

    def try_bundle(self, output_dir: str, **_kwargs: Any) -> bool:
        """Bundle the package into output_dir/python using pip or uv pip.

        Args:
            output_dir: The directory to install the package into.
            **_kwargs: CDK bundling options (ignored for local bundling).

        Returns:
            True if bundling succeeded, False otherwise.
        """
        python_dir = os.path.join(output_dir, "python")
        os.makedirs(python_dir, exist_ok=True)

        uv_bin = shutil.which("uv")
        if uv_bin:
            cmd = [
                uv_bin,
                "pip",
                "install",
                ".",
                "-t",
                python_dir,
                "--no-cache-dir",
                "--quiet",
                "--python",
                sys.executable,
            ]
        else:
            cmd = [
                sys.executable,
                "-m",
                "pip",
                "install",
                ".",
                "-t",
                python_dir,
                "--no-cache-dir",
                "--quiet",
            ]

        result = subprocess.run(cmd, cwd=self._source_dir, check=False)  # noqa: S603
        return result.returncode == 0


class HelloStack(cdk.Stack):
    """Stack that deploys the Hello Lambda behind an API Gateway REST API.

    Architecture:
    - A Lambda Layer containing third-party and shared dependencies.
    - A Lambda function with only the handler code.
    - An API Gateway REST API routing GET /hello to the Lambda.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Layer: bundle shared package dependencies
        shared_layer = lambda_.LayerVersion(
            self,
            "SharedLayer",
            code=lambda_.Code.from_asset(
                SHARED_DIR,
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=PipLocalBundler(SHARED_DIR),
                    command=[
                        "bash",
                        "-c",
                        "pip install . -t /asset-output/python --no-cache-dir --quiet",
                    ],
                ),
            ),
            compatible_runtimes=[lambda_.Runtime.PYTHON_3_13],
            description="Shared utilities layer for Hello Lambda",
        )

        # Lambda function: only the handler code (no deps — deps are in the layer)
        hello_fn = lambda_.Function(
            self,
            "HelloFunction",
            runtime=lambda_.Runtime.PYTHON_3_13,
            handler="hello.handler.handler",
            code=lambda_.Code.from_asset(
                os.path.join(LAMBDA_DIR, "src"),
            ),
            layers=[shared_layer],
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
