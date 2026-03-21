# python-aws-monorepo-boilerplate

> Python 3.13 monorepo boilerplate for serverless AWS applications — powered by uv workspaces, Ruff linting, and AWS CDK.

[![CI](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml/badge.svg)](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml)

---

## Tech Stack

| Tool | Role |
|------|------|
| Python 3.13 | Language |
| [uv](https://docs.astral.sh/uv/) | Package manager & workspace manager |
| [Ruff](https://docs.astral.sh/ruff/) | Linter & formatter |
| [pytest](https://docs.pytest.org/en/stable/) | Test framework |
| [mypy](https://mypy-lang.org/) | Static type checker |
| [AWS CDK (Python)](https://docs.aws.amazon.com/cdk/v2/guide/home.html) | Infrastructure as Code |

---

## Repository Structure

```
python-aws-monorepo-boilerplate/
│
├── .github/
│   └── workflows/
│       └── ci.yml              # Lint, type-check, test, CDK synth on push/PR
│
├── packages/
│   └── shared/                 # Internal shared utility library
│       ├── pyproject.toml
│       ├── src/shared/
│       │   ├── __init__.py
│       │   └── response.py     # build_response() helper
│       └── tests/
│
├── lambdas/
│   └── hello/                  # Example Lambda behind API Gateway
│       ├── pyproject.toml
│       ├── src/hello/
│       │   ├── __init__.py
│       │   └── handler.py      # Lambda entry point
│       └── tests/
│
├── infra/
│   ├── pyproject.toml
│   ├── cdk.json                # CDK app config
│   ├── app.py                  # CDK app entrypoint
│   └── stacks/
│       ├── __init__.py
│       └── hello_stack.py      # API Gateway + Lambda + Layer stack
│
├── scripts/
│   └── bootstrap.sh            # One-command dev setup
│
├── pyproject.toml              # Root uv workspace config + dev tools
├── .python-version             # 3.13
├── ruff.toml                   # Ruff lint + format config
├── mypy.ini                    # mypy strict config
└── .gitignore
```

---

## Getting Started

### Prerequisites

- [uv](https://docs.astral.sh/uv/getting-started/installation/) — Python package & workspace manager
- [Node.js](https://nodejs.org/) (≥18) — Required for the AWS CDK CLI
- [AWS CLI](https://aws.amazon.com/cli/) — Required for CDK deploy (not needed for `cdk synth`)

### One-Command Setup

```bash
bash scripts/bootstrap.sh
```

This will:
1. Install Python 3.13 (via uv)
2. Lock and install all workspace dependencies
3. Install the AWS CDK CLI via npm

### Manual Setup

```bash
# Install Python 3.13
uv python install 3.13

# Lock dependencies
uv lock

# Install all workspace packages
uv sync --all-packages
```

---

## Development

### Linting

```bash
uv run ruff check .
```

### Formatting

```bash
# Check only
uv run ruff format --check .

# Auto-fix
uv run ruff format .
```

### Type Checking

```bash
uv run mypy packages/ lambdas/
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=term-missing

# Run tests for a specific package
uv run pytest packages/shared/tests/
uv run pytest lambdas/hello/tests/
```

---

## CDK Infrastructure

### Prerequisites

Install the CDK CLI:

```bash
npm install -g aws-cdk
```

### Synthesise CloudFormation Template

No AWS credentials are needed for synth:

```bash
cd infra
uv run cdk synth
```

### Bootstrap AWS Environment (first-time only)

```bash
cd infra
uv run cdk bootstrap
```

### Deploy to AWS

```bash
cd infra
uv run cdk deploy
```

### Destroy Stack

```bash
cd infra
uv run cdk destroy
```

---

## Architecture

The `hello` stack provisions:

- **AWS Lambda Layer** — Contains the `shared` utility package and its dependencies, keeping the Lambda deployment package small.
- **AWS Lambda Function** — Contains only the handler code (`lambdas/hello/src/`). The layer is attached at runtime.
- **API Gateway REST API** — Routes `GET /hello` to the Lambda function. An optional `name` query parameter customises the greeting.

```
Client → API Gateway (GET /hello?name=Alice) → Lambda (hello.handler.handler) → 200 {"message": "Hello, Alice!"}
```

---

## Adding a New Lambda

1. Create a new package under `lambdas/`:
   ```bash
   mkdir -p lambdas/myfunction/src/myfunction lambdas/myfunction/tests
   ```
2. Add a `pyproject.toml` (copy from `lambdas/hello/pyproject.toml` and adjust the name).
3. Add the workspace member in the root `pyproject.toml` (the `lambdas/*` glob covers it automatically).
4. Write your handler in `lambdas/myfunction/src/myfunction/handler.py`.
5. Add a corresponding CDK stack in `infra/stacks/`.
6. Register the new stack in `infra/app.py`.

---

## License

[MIT](LICENSE)
