"""AWS CDK stack for the Users API Gateway + Lambda + Layer deployment."""

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


class UsersStack(cdk.Stack):
    """Stack that deploys the Users CRUD Lambdas behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            "UsersApi",
            rest_api_name="users-api",
            description="API Gateway for Users Lambdas",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        users_resource = api.root.add_resource("users")
        user_id_resource = users_resource.add_resource("{id}")

        users_create_fn = self._create_function(
            "UsersCreate",
            os.path.join(REPO_ROOT, "lambdas", "users_create"),
            "users_create.handler.handler",
            "Create User Lambda function",
        )
        users_get_fn = self._create_function(
            "UsersGet",
            os.path.join(REPO_ROOT, "lambdas", "users_get"),
            "users_get.handler.handler",
            "Get User Lambda function",
        )
        users_list_fn = self._create_function(
            "UsersList",
            os.path.join(REPO_ROOT, "lambdas", "users_list"),
            "users_list.handler.handler",
            "List Users Lambda function",
        )
        users_update_fn = self._create_function(
            "UsersUpdate",
            os.path.join(REPO_ROOT, "lambdas", "users_update"),
            "users_update.handler.handler",
            "Update User Lambda function",
        )
        users_delete_fn = self._create_function(
            "UsersDelete",
            os.path.join(REPO_ROOT, "lambdas", "users_delete"),
            "users_delete.handler.handler",
            "Delete User Lambda function",
        )

        users_resource.add_method("POST", apigw.LambdaIntegration(users_create_fn))
        users_resource.add_method("GET", apigw.LambdaIntegration(users_list_fn))
        user_id_resource.add_method("GET", apigw.LambdaIntegration(users_get_fn))
        user_id_resource.add_method("PUT", apigw.LambdaIntegration(users_update_fn))
        user_id_resource.add_method("DELETE", apigw.LambdaIntegration(users_delete_fn))

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
