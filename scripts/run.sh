#!/usr/bin/env bash
# Run File Search from source (Linux / macOS)
# Synchronizes and runs through the canonical locked uv environment.
# Usage: ./scripts/run.sh [--debug] [other options]

set -euo pipefail

# Always run from the repository root (parent of scripts/)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v uv >/dev/null 2>&1; then
    echo "Error: uv is required. See https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

exec uv run --locked python -m filesearch "$@"
