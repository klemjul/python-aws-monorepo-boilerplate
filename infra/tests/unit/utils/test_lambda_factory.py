"""Unit tests for infra/src/infra/utils/lambda_factory.py."""

import os
import sys
from unittest.mock import MagicMock, patch

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Template
from infra.utils.bundler import REPO_ROOT
from infra.utils.lambda_factory import create_lambda_function

HELLO_DIR = os.path.join(REPO_ROOT, "lambdas", "hello")


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


def _make_template_with_factory(
    logical_id: str, handler: str, description: str
) -> Template:
    """Synthesise a minimal stack using create_lambda_function and return its template."""  # noqa: E501
    export_mock, install_mock = _make_mock_pair()
    results = iter([export_mock, install_mock])

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", side_effect=_fake_run),
        patch("infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack = cdk.Stack(app, "TestStack")
        create_lambda_function(stack, logical_id, HELLO_DIR, handler, description)
        return Template.from_stack(stack)


@pytest.fixture
def template() -> Template:
    return _make_template_with_factory(
        "Hello", "hello.handler.handler", "Hello World Lambda function"
    )


def test_creates_lambda_function(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_creates_layer(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_lambda_runtime(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Runtime": "python3.13"},
    )


def test_lambda_handler(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Handler": "hello.handler.handler"},
    )


def test_lambda_memory(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"MemorySize": 256},
    )


def test_lambda_timeout(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Timeout": 30},
    )


def test_lambda_log_level_env(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Environment": {"Variables": {"LOG_LEVEL": "INFO"}}},
    )


def test_lambda_description(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Description": "Hello World Lambda function"},
    )


def test_layer_description_derived_from_function_description(
    template: Template,
) -> None:
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"Description": "Hello World Lambda function dependencies"},
    )


def test_layer_compatible_runtime(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"CompatibleRuntimes": ["python3.13"]},
    )


def test_logical_ids_use_prefix() -> None:
    """The layer and function CDK logical IDs must be prefixed with logical_id."""
    export_mock, install_mock = _make_mock_pair()
    results = iter([export_mock, install_mock])

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("infra.utils.bundler.subprocess.run", side_effect=_fake_run),
        patch("infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack = cdk.Stack(app, "TestStack")
        create_lambda_function(
            stack, "MyPrefix", HELLO_DIR, "hello.handler.handler", "My Lambda"
        )
        template = Template.from_stack(stack)

    resources = template.to_json()["Resources"]
    logical_ids = list(resources.keys())
    assert any("MyPrefix" in lid and "DepsLayer" in lid for lid in logical_ids), (
        f"Expected a logical ID containing 'MyPrefixDepsLayer', got: {logical_ids}"
    )
    assert any("MyPrefix" in lid and "Function" in lid for lid in logical_ids), (
        f"Expected a logical ID containing 'MyPrefixFunction', got: {logical_ids}"
    )
