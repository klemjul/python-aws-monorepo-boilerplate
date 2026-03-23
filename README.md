# python-aws-monorepo-boilerplate

> [!NOTE]
> POC Python monorepo boilerplate for serverless AWS applications, powered by uv, ruff, and AWS CDK.

[![CI](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml/badge.svg)](https://github.com/klemjul/python-aws-monorepo-boilerplate/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Python 3.13](https://img.shields.io/badge/python-3.13-blue.svg)](https://www.python.org/downloads/)
[![uv](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/uv/main/assets/badge/v0.json)](https://github.com/astral-sh/uv)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)

## Tech Stack

| Tool                                                                   | Role                                |
| ---------------------------------------------------------------------- | ----------------------------------- |
| Python 3.13                                                            | Language                            |
| [uv](https://docs.astral.sh/uv/)                                       | Package manager & workspace manager |
| [Ruff](https://docs.astral.sh/ruff/)                                   | Linter & formatter                  |
| [pytest](https://docs.pytest.org/en/stable/)                           | Test framework                      |
| [mypy](https://mypy-lang.org/)                                         | Static type checker                 |
| [AWS CDK (Python)](https://docs.aws.amazon.com/cdk/v2/guide/home.html) | Infrastructure as Code              |

---

## Repository Structure

```
python-aws-monorepo-boilerplate/
├── .github/workflows/ci.yml        # CI: lint, type-check, test, CDK synth
├── packages/
│   └── shared/                     # libraries
│   └── ...
├── lambdas/
│   └── hello/                      # lambdas
│   └── ...
├── infra/                          # AWS CDK app
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
uv run mypy packages/ lambdas/ infra/
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

## Infrastructure

### Deploy to AWS

```bash
uv run --directory infra cdk synth # generate cloud formation template
uv run --directory infra cdk deploy # deploy cfn stacks to aws
uv run --directory infra cdk destroy # destroy cfn stacks to aws
```

### How To

**New library** (`packages/<name>`):

- Create `packages/<name>/` with a `src/`, `tests/`, and `pyproject.toml` (copy `packages/shared` as a template).
- Add it as a dependency in any lambda's `pyproject.toml` via `[tool.uv.sources]`.

**New Lambda** (`lambdas/<name>`):

- Create `lambdas/<name>/` with a `src/`, `tests/`, and `pyproject.toml` (copy `lambdas/hello` as a template).
- Register the lambda in a stack under `infra/`.

## License

[MIT](LICENSE)
