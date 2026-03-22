SHELL := /bin/bash

# ─── Install ──────────────────────────────────────────────────────────────────

.PHONY: install
install:
	uv sync --all-packages

# ─── Lint & Format ────────────────────────────────────────────────────────────

.PHONY: lint
lint:
	uv run ruff check .

.PHONY: lint-fix
lint-fix:
	uv run ruff check --fix .

.PHONY: format
format:
	uv run ruff format --check .

.PHONY: format-fix
format-fix:
	uv run ruff format .

# ─── Type Checking ────────────────────────────────────────────────────────────

.PHONY: typecheck
typecheck:
	uv run mypy packages/*/src lambdas/*/src infra/src

# ─── Tests ────────────────────────────────────────────────────────────────────

.PHONY: test
test:
	uv run pytest

.PHONY: test-coverage
test-coverage:
	uv run pytest --cov --cov-report=term-missing

.PHONY: test-packages
test-packages:
	uv run pytest packages/ 

.PHONY: test-lambdas
test-lambdas:
	uv run pytest lambdas/

.PHONY: test-infra
test-infra:
	uv run pytest infra/

# ─── Code Quality (all-in-one) ────────────────────────────────────────────────

.PHONY: check
check: format lint typecheck test

.PHONY: fix
fix: format-fix lint-fix

# ─── CDK ──────────────────────────────────────────────────────────────────────

.PHONY: cdk-synth
cdk-synth: ## Synthesize CDK CloudFormation templates
	uv run --directory infra cdk synth

.PHONY: cdk-diff
cdk-diff: ## Show CDK diff against deployed stack
	uv run --directory infra cdk diff

.PHONY: cdk-deploy
cdk-deploy: ## Deploy all CDK stacks
	uv run --directory infra cdk deploy

.PHONY: cdk-destroy
cdk-destroy: ## Destroy all CDK stacks
	uv run --directory infra cdk destroy

.PHONY: cdk-ls
cdk-ls: ## List all CDK stacks
	uv run --directory infra cdk ls

