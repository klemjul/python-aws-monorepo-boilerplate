"""AWS CDK stack for the Orders API Gateway + Lambda + Layer deployment."""

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


class OrdersStack(cdk.Stack):
    """Stack that deploys the Orders CRUD Lambdas behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            "OrdersApi",
            rest_api_name="orders-api",
            description="API Gateway for Orders Lambdas",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        orders_resource = api.root.add_resource("orders")
        order_id_resource = orders_resource.add_resource("{id}")

        orders_create_fn = self._create_function(
            "OrdersCreate",
            os.path.join(REPO_ROOT, "lambdas", "orders_create"),
            "orders_create.handler.handler",
            "Create Order Lambda function",
        )
        orders_get_fn = self._create_function(
            "OrdersGet",
            os.path.join(REPO_ROOT, "lambdas", "orders_get"),
            "orders_get.handler.handler",
            "Get Order Lambda function",
        )
        orders_list_fn = self._create_function(
            "OrdersList",
            os.path.join(REPO_ROOT, "lambdas", "orders_list"),
            "orders_list.handler.handler",
            "List Orders Lambda function",
        )
        orders_update_fn = self._create_function(
            "OrdersUpdate",
            os.path.join(REPO_ROOT, "lambdas", "orders_update"),
            "orders_update.handler.handler",
            "Update Order Lambda function",
        )

        orders_resource.add_method("POST", apigw.LambdaIntegration(orders_create_fn))
        orders_resource.add_method("GET", apigw.LambdaIntegration(orders_list_fn))
        order_id_resource.add_method("GET", apigw.LambdaIntegration(orders_get_fn))
        order_id_resource.add_method("PUT", apigw.LambdaIntegration(orders_update_fn))

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
