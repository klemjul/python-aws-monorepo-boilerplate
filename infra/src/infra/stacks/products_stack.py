"""AWS CDK stack for the Products API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function


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

        products_create_fn = create_lambda_function(
            self,
            "ProductsCreate",
            os.path.join(REPO_ROOT, "lambdas", "products_create"),
            "products_create.handler.handler",
            "Create Product Lambda function",
        )
        products_get_fn = create_lambda_function(
            self,
            "ProductsGet",
            os.path.join(REPO_ROOT, "lambdas", "products_get"),
            "products_get.handler.handler",
            "Get Product Lambda function",
        )
        products_list_fn = create_lambda_function(
            self,
            "ProductsList",
            os.path.join(REPO_ROOT, "lambdas", "products_list"),
            "products_list.handler.handler",
            "List Products Lambda function",
        )
        products_update_fn = create_lambda_function(
            self,
            "ProductsUpdate",
            os.path.join(REPO_ROOT, "lambdas", "products_update"),
            "products_update.handler.handler",
            "Update Product Lambda function",
        )
        products_delete_fn = create_lambda_function(
            self,
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
