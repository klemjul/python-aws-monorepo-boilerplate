"""AWS CDK stack for the Hello API Gateway + Lambda + Layer deployment."""

import os
from typing import Any

import aws_cdk as cdk
from aws_cdk import aws_apigateway as apigw
from aws_cdk import aws_dynamodb as dynamodb
from constructs import Construct

from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function

LAMBDA_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")


class HelloStack(cdk.Stack):
    """Stack that deploys the Hello Lambda behind an API Gateway REST API."""

    def __init__(self, scope: Construct, construct_id: str, **kwargs: Any) -> None:
        super().__init__(scope, construct_id, **kwargs)

        greetings_table = dynamodb.Table(
            self,
            "GreetingsTable",
            partition_key=dynamodb.Attribute(
                name="id",
                type=dynamodb.AttributeType.STRING,
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=cdk.RemovalPolicy.DESTROY,
        )

        hello_fn = create_lambda_function(
            self,
            "Hello",
            LAMBDA_DIR,
            "hello.handler.handler",
            "Hello World Lambda function",
        )
        hello_fn.add_environment("GREETINGS_TABLE", greetings_table.table_name)
        greetings_table.grant_write_data(hello_fn)

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
        hello_resource.add_method("POST", hello_integration)

        cdk.CfnOutput(self, "ApiUrl", value=api.url, description="API Gateway URL")
