"""CDK assertion tests for HelloStack."""

import sys
from unittest.mock import MagicMock, patch

import aws_cdk as cdk
import pytest
from aws_cdk.assertions import Capture, Template
from infra.stacks.hello_stack import HelloStack


def _make_template(stack_id: str = "TestStack") -> Template:
    """Synthesise HelloStack and return its CloudFormation template.

    subprocess.run and shutil.which are patched so that DepsBundler.try_bundle
    runs its real code path and returns True without invoking uv or writing files
    (os.makedirs is NOT patched so the output dir is still created correctly).

    subprocess.run is called twice:
      1. ``uv export`` — must return stdout with requirements text and rc=0.
      2. ``uv pip install -r`` — must return rc=0.
    """
    export_mock = MagicMock()
    export_mock.returncode = 0
    export_mock.stdout = "aws-lambda-powertools==3.26.0\n"
    export_mock.stderr = ""

    install_mock = MagicMock()
    install_mock.returncode = 0
    install_mock.stdout = ""
    install_mock.stderr = ""

    results = iter([export_mock, install_mock])

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("src.infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("src.infra.utils.bundler.subprocess.run", side_effect=_fake_run),
        patch("src.infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack = HelloStack(app, stack_id)
        return Template.from_stack(stack)


@pytest.fixture
def template() -> Template:
    return _make_template()


# ---------------------------------------------------------------------------
# Lambda function
# ---------------------------------------------------------------------------


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


# ---------------------------------------------------------------------------
# Lambda Layer
# ---------------------------------------------------------------------------


def test_lambda_layer_exists(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::LayerVersion", 1)


def test_lambda_layer_compatible_runtime(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"CompatibleRuntimes": ["python3.13"]},
    )


def test_lambda_layer_description(template: Template) -> None:
    template.has_resource_properties(
        "AWS::Lambda::LayerVersion",
        {"Description": "Hello Lambda runtime dependencies"},
    )


def test_lambda_uses_layer(template: Template) -> None:
    """The Lambda function must reference at least one layer."""
    layer_capture = Capture()
    template.has_resource_properties(
        "AWS::Lambda::Function",
        {"Layers": layer_capture},
    )
    assert len(layer_capture.as_array()) >= 1


# ---------------------------------------------------------------------------
# API Gateway
# ---------------------------------------------------------------------------


def test_api_gateway_exists(template: Template) -> None:
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


def test_api_gateway_name(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ApiGateway::RestApi",
        {"Name": "hello-api"},
    )


def test_api_gateway_hello_resource(template: Template) -> None:
    """A /hello path part must exist."""
    template.has_resource_properties(
        "AWS::ApiGateway::Resource",
        {"PathPart": "hello"},
    )


def test_api_gateway_get_method(template: Template) -> None:
    """A GET method must be defined (on the /hello resource)."""
    template.has_resource_properties(
        "AWS::ApiGateway::Method",
        {"HttpMethod": "GET"},
    )


def test_api_gateway_prod_stage(template: Template) -> None:
    template.has_resource_properties(
        "AWS::ApiGateway::Stage",
        {"StageName": "prod"},
    )


# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------


def test_api_url_output_exists(template: Template) -> None:
    outputs = template.find_outputs("ApiUrl")
    assert outputs, "Expected 'ApiUrl' CfnOutput to exist in the template"


# ---------------------------------------------------------------------------
# IAM - Lambda execution role
# ---------------------------------------------------------------------------


def test_lambda_execution_role_exists(template: Template) -> None:
    template.has_resource_properties(
        "AWS::IAM::Role",
        {
            "AssumeRolePolicyDocument": {
                "Statement": [
                    {
                        "Action": "sts:AssumeRole",
                        "Effect": "Allow",
                        "Principal": {"Service": "lambda.amazonaws.com"},
                    }
                ]
            }
        },
    )


# ---------------------------------------------------------------------------
# Resource counts
# ---------------------------------------------------------------------------


def test_single_lambda_function(template: Template) -> None:
    template.resource_count_is("AWS::Lambda::Function", 1)


def test_single_rest_api(template: Template) -> None:
    template.resource_count_is("AWS::ApiGateway::RestApi", 1)


# ---------------------------------------------------------------------------
# HelloStack - smoke checks
# ---------------------------------------------------------------------------


def test_stack_can_be_instantiated() -> None:
    """HelloStack must be instantiatable without exceptions."""
    # _make_template raises if HelloStack can't be instantiated
    template = _make_template("SmokeStack")
    assert template is not None


def test_multiple_stacks_are_independent() -> None:
    """Two HelloStack instances in the same app must not share state."""
    export_mock = MagicMock()
    export_mock.returncode = 0
    export_mock.stdout = "aws-lambda-powertools==3.26.0\n"
    export_mock.stderr = ""
    install_mock = MagicMock()
    install_mock.returncode = 0
    install_mock.stdout = ""
    install_mock.stderr = ""
    results = iter([export_mock, install_mock, export_mock, install_mock])

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("src.infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch("src.infra.utils.bundler.subprocess.run", side_effect=_fake_run),
        patch("src.infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack_a = HelloStack(app, "StackA")
        stack_b = HelloStack(app, "StackB")
    assert stack_a.stack_name != stack_b.stack_name


# ---------------------------------------------------------------------------
# Bundler integration (subprocess invoked during synth)
# ---------------------------------------------------------------------------


def test_hello_stack_invokes_uv_during_synth() -> None:
    """subprocess.run must be called at least once when synthesising the stack."""
    export_mock = MagicMock()
    export_mock.returncode = 0
    export_mock.stdout = "aws-lambda-powertools==3.26.0\n"
    export_mock.stderr = ""
    install_mock = MagicMock()
    install_mock.returncode = 0
    install_mock.stdout = ""
    install_mock.stderr = ""
    results = iter([export_mock, install_mock])

    def _fake_run(cmd: list[str], **kwargs: object) -> MagicMock:
        return next(results)

    with (
        patch.object(sys, "platform", "linux"),
        patch("src.infra.utils.bundler.shutil.which", return_value="/usr/bin/uv"),
        patch(
            "src.infra.utils.bundler.subprocess.run", side_effect=_fake_run
        ) as mock_run,
        patch("src.infra.utils.bundler.os.unlink"),
    ):
        app = cdk.App()
        stack = HelloStack(app, "BundlerStack")
        Template.from_stack(stack)
    mock_run.assert_called()
