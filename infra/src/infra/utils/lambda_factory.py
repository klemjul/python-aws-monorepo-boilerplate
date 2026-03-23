"""Factory utility for creating Lambda functions with a dependency layer."""

import os
from typing import cast

import aws_cdk as cdk
from aws_cdk import aws_lambda as lambda_
from constructs import Construct

from infra.utils.bundler import DepsBundler, deps_hash


def create_lambda_function(
    scope: Construct,
    logical_id: str,
    lambda_dir: str,
    handler: str,
    description: str,
) -> lambda_.Function:
    """Create a Lambda function with a bundled dependency layer.

    A ``LayerVersion`` is created from *lambda_dir* using :class:`DepsBundler`
    for local bundling, and is attached to the returned ``Function``.

    Args:
        scope: The CDK construct scope (typically a ``Stack``).
        logical_id: Prefix used for the CDK logical IDs of the layer and
            function (e.g. ``"UsersCreate"``).
        lambda_dir: Absolute path to the lambda package directory.
        handler: Python dotted handler path (e.g.
            ``"users_create.handler.handler"``).
        description: Human-readable description for the Lambda function;
            the layer description is derived from this by appending
            ``" dependencies"``.

    Returns:
        The configured :class:`aws_cdk.aws_lambda.Function`.
    """
    layer = lambda_.LayerVersion(
        scope,
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
        scope,
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
