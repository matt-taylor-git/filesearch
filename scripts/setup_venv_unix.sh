#!/usr/bin/env bash
# Compatibility wrapper for the canonical uv development setup.

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required. See https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "Synchronizing the locked File Search development environment..."
uv sync --locked
uv run pre-commit install

echo
echo "Development environment ready."
echo "Run the app:   uv run python -m filesearch"
echo "Run tests:     uv run pytest"
echo "Format code:   uv run black src/ tests/"
echo "Lint code:     uv run flake8 src/ tests/"
