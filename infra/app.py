"""AWS CDK application entrypoint."""

import aws_cdk as cdk
from infra.stacks.hello_stack import HelloStack

app = cdk.App()
HelloStack(app, "HelloStack")
app.synth()
