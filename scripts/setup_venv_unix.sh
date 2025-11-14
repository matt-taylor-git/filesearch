#!/bin/bash
# Virtual environment setup script for Linux/macOS

set -e

echo "Setting up File Search development environment..."

# Check if Python 3.9+ is available
python_version=$(python3 --version 2>&1 | awk '{print $2}')
required_version="3.9"

if ! python3 -c "import sys; exit(0 if sys.version_info >= (3, 9) else 1)"; then
    echo "Error: Python 3.9 or higher is required. Found: $python_version"
    exit 1
fi

echo "✓ Python $python_version detected"

# Create virtual environment
echo "Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip

# Install runtime dependencies
echo "Installing runtime dependencies..."
pip install -r requirements.txt

# Install development dependencies
echo "Installing development dependencies..."
pip install -r requirements-dev.txt

# Install pre-commit hooks
echo "Installing pre-commit hooks..."
pre-commit install

echo ""
echo "✓ Development environment setup complete!"
echo ""
echo "To activate the virtual environment in future sessions:"
echo "  source venv/bin/activate"
echo ""
echo "To run the application:"
echo "  python -m filesearch"
echo ""
echo "To run tests:"
echo "  pytest"
echo ""
echo "To format code:"
echo "  black src/ tests/"
echo ""
echo "To lint code:"
echo "  flake8 src/ tests/"
