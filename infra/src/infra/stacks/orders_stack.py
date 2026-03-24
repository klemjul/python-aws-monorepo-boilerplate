"""AWS CDK stack for the Orders API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function


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

        orders_create_fn = create_lambda_function(
            self,
            "OrdersCreate",
            os.path.join(REPO_ROOT, "lambdas", "orders_create"),
            "orders_create.handler.handler",
            "Create Order Lambda function",
        )
        orders_get_fn = create_lambda_function(
            self,
            "OrdersGet",
            os.path.join(REPO_ROOT, "lambdas", "orders_get"),
            "orders_get.handler.handler",
            "Get Order Lambda function",
        )
        orders_list_fn = create_lambda_function(
            self,
            "OrdersList",
            os.path.join(REPO_ROOT, "lambdas", "orders_list"),
            "orders_list.handler.handler",
            "List Orders Lambda function",
        )
        orders_update_fn = create_lambda_function(
            self,
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
