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
| [pre-commit](https://pre-commit.com/)                                  | Git hook manager                    |

---

## Repository Structure

```
python-aws-monorepo-boilerplate/
├── .github/workflows/ci.yml        # CI: lint, type-check, test, CDK synth
├── .pre-commit-config.yaml         # Pre-commit hooks (lint, format, branch name)
├── packages/
│   └── shared/                     # libraries
│   └── ...
├── lambdas/
│   └── hello/                      # lambdas
│   └── ...
├── scripts/
│   └── hello/                      # scripts
│   └── check_branch_name/          # pre-commit hook: validates branch names
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
uv run pytest scripts/hello_script/tests/
```

## Pre-commit Hooks

This repository ships a `.pre-commit-config.yaml` that enforces code quality on every commit:

| Hook                  | Purpose                                              |
| --------------------- | ---------------------------------------------------- |
| `trailing-whitespace` | Remove trailing whitespace                           |
| `end-of-file-fixer`   | Ensure files end with a newline                      |
| `check-yaml`          | Validate YAML syntax                                 |
| `check-added-large-files` | Reject accidental large-file commits            |
| `ruff`                | Lint and auto-fix Python code                        |
| `ruff-format`         | Format Python code                                   |
| `check-branch-name`   | Enforce the branch naming convention (see below)     |

### Setup

```bash
pip install pre-commit   # or: uv tool install pre-commit
pre-commit install
```

After that, hooks run automatically on every `git commit`.

### Branch Naming Convention

The `check-branch-name` hook (implemented in `scripts/check_branch_name/`) rejects commits
made on branches that do not match the expected pattern:

```
main | master | develop
<type>/<description>
```

Allowed types: `feature`, `bugfix`, `hotfix`, `release`, `chore`, `docs`, `refactor`, `test`

The `<description>` must use only **lowercase letters, digits, hyphens, dots, or slashes** and
must not be empty.

**Valid examples**

```
main
feature/add-login
bugfix/fix-null-pointer
hotfix/urgent-security-patch
release/1.2.0
chore/update-deps
```

**Invalid examples**

```
my-feature            # missing type prefix
Feature/add-login     # uppercase type
feature/             # empty description
unknown/my-branch     # unrecognised type
```

You can also run the hook manually at any time:

```bash
uv run check-branch-name
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

**New Script** (`scripts/<name>`):

- Create `scripts/<name>/` with a `src/`, `tests/`, and `pyproject.toml` (copy `scripts/hello_script` as a template).
- Add a `[project.scripts]` entry in `pyproject.toml` to declare the CLI entry point.
- Add `scripts/<name>/tests` to `testpaths` and `scripts/<name>/src` to `mypy_path` in the root `pyproject.toml`.

## License

[MIT](LICENSE)
