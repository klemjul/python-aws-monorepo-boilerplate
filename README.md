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
├── pyproject.toml              # Root uv workspace config + dev tools
├── .python-version             # 3.13
├── ruff.toml                   # Ruff lint + format config
├── mypy.ini                    # mypy strict config
└── .gitignore
```

---

## Getting Started

### Prerequisites

| Tool | Installation |
|------|-------------|
| **uv** | See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/) |
| **Node.js** (≥18) | Required for the AWS CDK CLI. Use [nvm](https://github.com/nvm-sh/nvm) (Linux/macOS), [nvm-windows](https://github.com/coreybutler/nvm-windows) (Windows), or the [official installer](https://nodejs.org/) |
| **AWS CLI** | Required for `cdk deploy`. See [AWS CLI installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (not needed for `cdk synth`) |

### Setup

**Linux / macOS**

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Install Python 3.13 and workspace dependencies
uv python install 3.13
uv sync --all-packages

# Install the CDK CLI (requires Node.js)
npm install -g aws-cdk
```

**Windows (PowerShell)**

```powershell
# Install uv
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"

# Install Python 3.13 and workspace dependencies
uv python install 3.13
uv sync --all-packages

# Install the CDK CLI (requires Node.js)
npm install -g aws-cdk
```

> **Note:** All `uv` and `uv run` commands work identically on Linux, macOS, and Windows.

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

- **HelloDepsLayer** — A Lambda Layer containing all of the `hello` lambda's runtime dependencies (as declared in `lambdas/hello/pyproject.toml`). This keeps the Lambda deployment package small. Add any new runtime dependency to `lambdas/hello/pyproject.toml` and it will automatically be bundled into this layer.
- **HelloFunction** — The Lambda function containing only the handler source code (`lambdas/hello/src/`). All imports are satisfied at runtime by the layer.
- **API Gateway REST API** — Routes `GET /hello` to the Lambda function. An optional `name` query parameter customises the greeting.

```
Client → API Gateway (GET /hello?name=Alice) → Lambda (hello.handler.handler) → 200 {"message": "Hello, Alice!"}
```

---

## Adding a New Lambda

1. Create a new package under `lambdas/`:
   ```bash
   # Linux / macOS
   mkdir -p lambdas/myfunction/src/myfunction lambdas/myfunction/tests

   # Windows (PowerShell)
   New-Item -ItemType Directory lambdas/myfunction/src/myfunction
   New-Item -ItemType Directory lambdas/myfunction/tests
   ```
2. Add a `pyproject.toml` (copy from `lambdas/hello/pyproject.toml` and adjust the name and dependencies).
3. The root `pyproject.toml` workspace glob `lambdas/*` picks it up automatically — run `uv lock` to update the lockfile.
4. Write your handler in `lambdas/myfunction/src/myfunction/handler.py`.
5. Add a corresponding CDK stack in `infra/stacks/`.
6. Register the new stack in `infra/app.py`.

---

## License

[MIT](LICENSE)
