"""AWS CDK stack for the Users API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from constructs import Construct

from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function


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

        users_create_fn = create_lambda_function(
            self,
            "UsersCreate",
            os.path.join(REPO_ROOT, "lambdas", "users_create"),
            "users_create.handler.handler",
            "Create User Lambda function",
        )
        users_get_fn = create_lambda_function(
            self,
            "UsersGet",
            os.path.join(REPO_ROOT, "lambdas", "users_get"),
            "users_get.handler.handler",
            "Get User Lambda function",
        )
        users_list_fn = create_lambda_function(
            self,
            "UsersList",
            os.path.join(REPO_ROOT, "lambdas", "users_list"),
            "users_list.handler.handler",
            "List Users Lambda function",
        )
        users_update_fn = create_lambda_function(
            self,
            "UsersUpdate",
            os.path.join(REPO_ROOT, "lambdas", "users_update"),
            "users_update.handler.handler",
            "Update User Lambda function",
        )
        users_delete_fn = create_lambda_function(
            self,
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
