"""AWS CDK application entrypoint."""

import aws_cdk as cdk
from infra.stacks.hello_stack import HelloStack
from infra.stacks.orders_stack import OrdersStack
from infra.stacks.products_stack import ProductsStack
from infra.stacks.reports_stack import ReportsStack
from infra.stacks.users_stack import UsersStack

app = cdk.App()
HelloStack(app, "HelloStack")
UsersStack(app, "UsersStack")
ProductsStack(app, "ProductsStack")
OrdersStack(app, "OrdersStack")
ReportsStack(app, "ReportsStack")
app.synth()
