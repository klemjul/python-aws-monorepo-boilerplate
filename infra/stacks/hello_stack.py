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

REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
LAMBDA_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")
SHARED_DIR = os.path.join(REPO_ROOT, "packages", "shared")


@jsii.implements(cdk.ILocalBundling)
class DepsBundler:
    """Local bundler that installs a Python package's dependencies with uv/pip.

    Packages are installed into ``output_dir/python`` so that the resulting
    directory can be used directly as a Lambda Layer source.

    Used as a fallback when Docker is not available (e.g. in CI synth).
    """

    def __init__(self, packages: list[str]) -> None:
        """Initialise the bundler with a list of package paths/names to install.

        Args:
            packages: Paths to local packages or PyPI package specs to install.
        """
        self._packages = packages

    def try_bundle(self, output_dir: str, _options: cdk.BundlingOptions) -> bool:
        """Install all packages into ``output_dir/python``.

        The jsii runtime calls this with two positional arguments.

        Args:
            output_dir: Destination directory for the bundled layer contents.
            _options: CDK bundling options passed by the jsii runtime (unused).

        Returns:
            True if all packages were installed successfully, False otherwise.
        """
        python_dir = os.path.join(output_dir, "python")
        os.makedirs(python_dir, exist_ok=True)

        uv_bin = shutil.which("uv")
        if uv_bin:
            cmd: list[str] = [
                uv_bin,
                "pip",
                "install",
                *self._packages,
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
                *self._packages,
                "-t",
                python_dir,
                "--no-cache-dir",
                "--quiet",
            ]

        result = subprocess.run(cmd, check=False)  # noqa: S603
        return result.returncode == 0


class HelloStack(cdk.Stack):
    """Stack that deploys the Hello Lambda behind an API Gateway REST API.

    Architecture:
    - A Lambda Layer containing all of hello's runtime dependencies.
    - A Lambda function with only the handler code (no bundled deps).
    - An API Gateway REST API routing GET /hello to the Lambda.
    """

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # HelloDepsLayer: all runtime deps from lambdas/hello/pyproject.toml
        # (currently: packages/shared). The lambda code zip contains only the
        # handler; this layer provides everything it imports at runtime.
        hello_deps_layer = lambda_.LayerVersion(
            self,
            "HelloDepsLayer",
            code=lambda_.Code.from_asset(
                SHARED_DIR,
                bundling=cdk.BundlingOptions(
                    image=lambda_.Runtime.PYTHON_3_13.bundling_image,
                    local=DepsBundler([SHARED_DIR]),
                    command=[
                        "bash",
                        "-c",
                        "pip install . -t /asset-output/python --no-cache-dir --quiet",
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
