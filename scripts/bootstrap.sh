#!/usr/bin/env bash
# bootstrap.sh — One-command dev setup for python-aws-monorepo-boilerplate
set -euo pipefail

echo "==> Checking for uv..."
if ! command -v uv &>/dev/null; then
    echo "uv not found. Installing uv..."
    pip install uv
fi

echo "==> Installing Python 3.13 (if needed)..."
uv python install 3.13

echo "==> Locking dependencies..."
uv lock

echo "==> Installing all workspace packages..."
uv sync --all-packages

echo "==> Installing AWS CDK CLI (requires Node.js / npm)..."
if command -v npm &>/dev/null; then
    npm install -g aws-cdk
else
    echo "WARNING: npm not found — skipping CDK CLI install. Install Node.js to use CDK."
fi

echo ""
echo "✅  Bootstrap complete!"
echo ""
echo "Useful commands:"
echo "  uv run ruff check .           # lint"
echo "  uv run ruff format .          # format"
echo "  uv run mypy packages/ lambdas/ # type-check"
echo "  uv run pytest                  # run tests"
echo "  cd infra && uv run cdk synth   # synth CDK"
echo "  cd infra && uv run cdk deploy  # deploy to AWS"
