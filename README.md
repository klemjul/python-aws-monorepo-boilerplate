# python-aws-monorepo-boilerplate

A production-ready Python monorepo template for building serverless AWS applications. It wires together the fastest modern Python tooling — **uv** for dependency management, **Ruff** for linting and formatting, **mypy** for static typing, **pytest** for testing, and **AWS CDK** for infrastructure as code — all in a single, consistent developer workflow.

[![CI](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml/badge.svg)](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Why This Stack?

| Pain point                          | Solution in this repo                                                                                                                    |
| ----------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------- |
| Slow installs & dependency hell     | **uv** resolves and installs packages orders of magnitude faster than pip/poetry and manages the entire workspace with a single lockfile. |
| Inconsistent code style             | **Ruff** replaces flake8, isort, pyupgrade, and black with a single Rust-powered tool. Linting and formatting in milliseconds.          |
| Runtime surprises                   | **mypy** in strict mode catches type errors before they reach production.                                                                |
| Shared code without publishing      | **uv workspaces** let `lambdas/` and `scripts/` import from `packages/` as first-class dependencies — no PyPI publishing required.      |
| IaC in a different language         | **AWS CDK (Python)** means your infrastructure lives in the same language and workspace as your application code, fully type-checked.    |
| Lambda dependency packaging         | The built-in `DepsBundler` uses `uv export` + `uv pip install` to build Lambda Layers locally with a deterministic, content-based hash. |

## Tech Stack

| Tool                                                                   | Role                                |
| ---------------------------------------------------------------------- | ----------------------------------- |
| Python 3.13                                                            | Language                            |
| [uv](https://docs.astral.sh/uv/)                                       | Package manager & workspace manager |
| [Ruff](https://docs.astral.sh/ruff/)                                   | Linter & formatter                  |
| [pytest](https://docs.pytest.org/en/stable/)                           | Test framework                      |
| [mypy](https://mypy-lang.org/)                                         | Static type checker                 |
| [AWS CDK (Python)](https://docs.aws.amazon.com/cdk/v2/guide/home.html) | Infrastructure as Code              |

## Repository Structure

```
python-aws-monorepo-boilerplate/
├── .github/workflows/ci.yml        # CI: lint, type-check, test, CDK synth
├── packages/
│   └── shared/                     # shared internal libraries
│   └── ...
├── lambdas/
│   └── hello/                      # Lambda functions
│   └── ...
├── scripts/
│   └── hello_script/               # CLI scripts
│   └── ...
├── infra/                          # AWS CDK app
│   ├── src/infra/stacks/           # CDK stack definitions
│   └── src/infra/utils/            # bundler & CDK helpers
├── pyproject.toml                  # Root uv workspace, dev tools, mypy config
├── ruff.toml                       # Ruff lint + format config
└── Makefile                        # developer convenience targets
```

## Getting Started

### Prerequisites

| Tool                  | Installation                                                                                                                                                      |
| --------------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **uv**                | See [uv installation docs](https://docs.astral.sh/uv/getting-started/installation/)                                                                               |
| **Node.js** (≥20 LTS) | See [nodejs.org](https://nodejs.org/)                                                                                                                             |
| **AWS CDK CLI** (≥2)  | See [aws/aws-cdk](https://github.com/aws/aws-cdk)                                                                                                                 |
| **AWS CLI**           | Required for `cdk deploy`. See [AWS CLI installation](https://docs.aws.amazon.com/cli/latest/userguide/getting-started-install.html) (not needed for `cdk synth`) |

### Setup

```bash
uv python install 3.13
uv sync --all-packages
```

## Development

All commands below have `make` equivalents (e.g. `make lint`, `make typecheck`, `make test`). Run `make check` to execute all checks in sequence.

### Linting

```bash
uv run ruff check .

# Auto-fix
uv run ruff check --fix .
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
uv run mypy packages/*/src lambdas/*/src scripts/*/src infra/src
```

### Running Tests

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov --cov-report=term-missing

# Run tests for a specific area
uv run pytest packages/shared/tests/
uv run pytest lambdas/hello/tests/
uv run pytest scripts/hello_script/tests/
uv run pytest infra/tests/
```

## Infrastructure

### CDK Commands

```bash
uv run --directory infra cdk ls       # list all stacks
uv run --directory infra cdk synth    # generate CloudFormation templates
uv run --directory infra cdk diff     # show diff against the deployed stack
uv run --directory infra cdk deploy   # deploy stacks to AWS
uv run --directory infra cdk destroy  # destroy deployed stacks
```

> `make cdk-synth`, `make cdk-diff`, `make cdk-deploy`, `make cdk-destroy`, and `make cdk-ls` are available as Makefile shortcuts.

### Lambda Dependency Bundling

Lambda runtime dependencies are packaged as a **Lambda Layer** by the `DepsBundler` utility (`infra/src/infra/utils/bundler.py`). It runs `uv export` to resolve transitive dependencies and `uv pip install` to install them locally. The layer asset hash is derived from the Lambda's `pyproject.toml` and the source of any workspace package dependencies, so the layer is only rebuilt when its inputs actually change.

### How To

**New package / shared library** (`packages/<name>`):

1. Copy `packages/shared/` as a template: create `packages/<name>/` with `src/<name>/`, `tests/`, and `pyproject.toml`.
2. Add `packages/<name>/src` to `mypy_path` in the root `pyproject.toml`.
3. Add `packages/<name>/tests` to `testpaths` in the root `pyproject.toml`.
4. Declare it as a workspace dependency in any consumer's `pyproject.toml` via `[tool.uv.sources]`:
   ```toml
   [tool.uv.sources]
   <name> = { workspace = true }
   ```
5. Run `uv sync --all-packages` to update the lockfile.

**New Lambda** (`lambdas/<name>`):

1. Copy `lambdas/hello/` as a template: create `lambdas/<name>/` with `src/<name>/`, `tests/`, and `pyproject.toml`.
2. Add `lambdas/<name>/src` to `mypy_path` in the root `pyproject.toml`.
3. Add `lambdas/<name>/tests` to `testpaths` in the root `pyproject.toml`.
4. Run `uv sync --all-packages` to update the lockfile.
5. Create a CDK stack (or add to an existing one) under `infra/src/infra/stacks/` that references the new lambda directory and uses `DepsBundler` for packaging (see `hello_stack.py` as a reference).
6. Register the stack in `infra/app.py`.

**New Script** (`scripts/<name>`):

1. Copy `scripts/hello_script/` as a template: create `scripts/<name>/` with `src/<name>/`, `tests/`, and `pyproject.toml`.
2. Declare the CLI entry point in `scripts/<name>/pyproject.toml`:
   ```toml
   [project.scripts]
   <name> = "<name>.main:main"
   ```
3. Add `scripts/<name>/src` to `mypy_path` in the root `pyproject.toml`.
4. Add `scripts/<name>/tests` to `testpaths` in the root `pyproject.toml`.
5. Run `uv sync --all-packages` to update the lockfile and register the new entry point.
6. Run the script with `uv run <name>`.

**New CDK stack** (`infra/src/infra/stacks/<name>_stack.py`):

1. Create `infra/src/infra/stacks/<name>_stack.py` following the pattern in `hello_stack.py`.
2. Register the new stack class in `infra/app.py`:
   ```python
   from infra.stacks.<name>_stack import <Name>Stack
   <Name>Stack(app, "<Name>Stack")
   ```
3. Run `uv run --directory infra cdk synth` to verify the template synthesises correctly.

## License

[MIT](LICENSE)
