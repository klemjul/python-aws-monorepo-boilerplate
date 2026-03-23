"""CDK assertion tests for OrdersStack."""

import sys
from unittest.mock import MagicMock, patch

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template
from infra.stacks.orders_stack import OrdersStack


def _make_mock_pair() -> tuple[MagicMock, MagicMock]:
    export_mock = MagicMock()
    export_mock.returncode = 0
    export_mock.stdout = "aws-lambda-powertools==3.26.0\n"
    export_mock.stderr = ""

    install_mock = MagicMock()
    install_mock.returncode = 0
    install_mock.stdout = ""
    install_mock.stderr = ""

    return export_mock, install_mock


def _make_template(stack_id: str = "TestStack") -> Template:
    """Synthesise OrdersStack and return its CloudFormation template."""
    pairs = [_make_mock_pair() for _ in range(4)]
    results = iter(mock for pair in pairs for mock in pair)

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", side_effect=_fake_run),
        patch("infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack = OrdersStack(app, stack_id)
        return Template.from_stack(stack)


@pytest.fixture
def template() -> Template:
    return _make_template()


def test_lambda_count(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::Function", 4)


def test_lambda_layer_count(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::LayerVersion", 4)


def test_api_gateway_exists(template: Template) -> None:
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_gateway_name(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ApiGateway::RestApi",
        {"Name": "orders-api"},
    )


def test_api_gateway_prod_stage(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ApiGateway::Stage",
        {"StageName": "prod"},
    )


def test_api_url_output_exists(template: Template) -> None:
    outputs = template.find_outputs("ApiUrl")
    assert outputs, "Expected 'ApiUrl' CfnOutput to exist in the template"


def test_lambda_runtime(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Runtime": "python3.13"},
    )


def test_lambda_memory(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"MemorySize": 256},
    )


def test_lambda_create_order_handler(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Handler": "orders_create.handler.handler"},
    )


def test_lambda_list_orders_handler(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Handler": "orders_list.handler.handler"},
    )
