#!/usr/bin/env bash
# Run File Search from source (Linux / macOS)
# Creates a local venv and installs runtime deps if missing.
# Usage: ./scripts/run.sh [--debug] [other options]

set -euo pipefail

# Always run from the repository root (parent of scripts/)
ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

VENV_DIR=""
if [[ -x "venv/bin/python" ]]; then
    VENV_DIR="venv"
elif [[ -x ".venv/bin/python" ]]; then
    VENV_DIR=".venv"
fi

if [[ -z "$VENV_DIR" ]]; then
    echo "No virtual environment found. Setting one up..."
    echo

    if command -v python3 >/dev/null 2>&1; then
        BOOTSTRAP_PYTHON="python3"
    elif command -v python >/dev/null 2>&1; then
        BOOTSTRAP_PYTHON="python"
    else
        echo "Error: Python is not installed or not in PATH."
        echo "Install Python 3.9+ and try again."
        exit 1
    fi

    if ! "$BOOTSTRAP_PYTHON" -c "import sys; raise SystemExit(0 if sys.version_info >= (3, 9) else 1)"; then
        python_version="$("$BOOTSTRAP_PYTHON" --version 2>&1)"
        echo "Error: Python 3.9 or higher is required. Found: ${python_version}"
        exit 1
    fi

    python_version="$("$BOOTSTRAP_PYTHON" --version 2>&1 | awk '{print $2}')"
    echo "✓ Python ${python_version} detected"
    echo "Creating virtual environment in ./venv ..."
    "$BOOTSTRAP_PYTHON" -m venv venv

    VENV_DIR="venv"
    PYTHON_EXE="venv/bin/python"

    echo "Upgrading pip..."
    "$PYTHON_EXE" -m pip install --upgrade pip

    echo "Installing runtime dependencies..."
    "$PYTHON_EXE" -m pip install -r requirements.txt

    echo "Installing File Search package (editable)..."
    "$PYTHON_EXE" -m pip install -e .

    echo
    echo "✓ Virtual environment ready."
    echo
else
    PYTHON_EXE="${VENV_DIR}/bin/python"
fi

# Ensure the package is importable even if editable install is incomplete
export PYTHONPATH="${ROOT_DIR}/src${PYTHONPATH:+:${PYTHONPATH}}"

exec "$PYTHON_EXE" -m filesearch "$@"
