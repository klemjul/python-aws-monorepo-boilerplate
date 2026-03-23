"""AWS CDK stack for the Products API Gateway + Lambda + Layer deployment."""

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


class ProductsStack(cdk.Stack):
    """Stack that deploys the Products CRUD Lambdas behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        api = apigw.RestApi(
            self,
            "ProductsApi",
            rest_api_name="products-api",
            description="API Gateway for Products Lambdas",
            deploy_options=apigw.StageOptions(stage_name="prod"),
        )

        products_resource = api.root.add_resource("products")
        product_id_resource = products_resource.add_resource("{id}")

        products_create_fn = self._create_function(
            "ProductsCreate",
            os.path.join(REPO_ROOT, "lambdas", "products_create"),
            "products_create.handler.handler",
            "Create Product Lambda function",
        )
        products_get_fn = self._create_function(
            "ProductsGet",
            os.path.join(REPO_ROOT, "lambdas", "products_get"),
            "products_get.handler.handler",
            "Get Product Lambda function",
        )
        products_list_fn = self._create_function(
            "ProductsList",
            os.path.join(REPO_ROOT, "lambdas", "products_list"),
            "products_list.handler.handler",
            "List Products Lambda function",
        )
        products_update_fn = self._create_function(
            "ProductsUpdate",
            os.path.join(REPO_ROOT, "lambdas", "products_update"),
            "products_update.handler.handler",
            "Update Product Lambda function",
        )
        products_delete_fn = self._create_function(
            "ProductsDelete",
            os.path.join(REPO_ROOT, "lambdas", "products_delete"),
            "products_delete.handler.handler",
            "Delete Product Lambda function",
        )

        products_resource.add_method(
            "POST", apigw.LambdaIntegration(products_create_fn)
        )
        products_resource.add_method("GET", apigw.LambdaIntegration(products_list_fn))
        product_id_resource.add_method("GET", apigw.LambdaIntegration(products_get_fn))
        product_id_resource.add_method(
            "PUT", apigw.LambdaIntegration(products_update_fn)
        )
        product_id_resource.add_method(
            "DELETE", apigw.LambdaIntegration(products_delete_fn)
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
