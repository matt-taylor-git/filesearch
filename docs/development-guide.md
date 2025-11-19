# Development Guide

## Overview

This guide provides comprehensive instructions for setting up, developing, testing, and contributing to the File Search application.

## Prerequisites

### System Requirements
- **Operating System**: Windows 10+, macOS 10.14+, or Linux (Ubuntu 18.04+)
- **Python**: Version 3.9 or higher
- **Memory**: Minimum 4GB RAM (8GB recommended)
- **Storage**: 100MB free disk space for application and dependencies

### Development Tools
- **Git**: For version control and repository management
- **Python IDE**: VS Code, PyCharm, or similar with Python support
- **Terminal**: Command line interface for running commands

## Setup Instructions

### 1. Clone Repository
```bash
git clone https://github.com/filesearch/filesearch.git
cd filesearch
```

### 2. Create Virtual Environment
```bash
# Windows
python -m venv venv
venv\Scripts\activate

# macOS/Linux
python3 -m venv venv
source venv/bin/activate
```

### 3. Install Dependencies
```bash
# Runtime dependencies
pip install -r requirements.txt

# Development dependencies (optional)
pip install -r requirements-dev.txt
```

### 4. Install Pre-commit Hooks
```bash
pre-commit install
```

### 5. Verify Installation
```bash
# Test application startup
python -m filesearch --help

# Run tests to verify environment
pytest
```

## Development Workflow

### Running the Application

#### Development Mode
```bash
# From source with debug logging
python -m filesearch --debug

# With specific log level
python -m filesearch --info
python -m filesearch --warning
```

#### Installed Mode
```bash
# If installed via pip
filesearch

# Show version
filesearch --version
```

### Code Quality Tools

#### Code Formatting
```bash
# Format all source files
black src/ tests/

# Check formatting without modifying
black --check src/ tests/

# Format specific file
black src/filesearch/core/search_engine.py
```

#### Import Sorting
```bash
# Sort imports in all files
isort src/ tests/

# Check import sorting
isort --check-only --profile=black src/ tests/
```

#### Linting
```bash
# Lint all source and test files
flake8 src/ tests/

# Lint with specific configuration
flake8 --max-line-length=88 --extend-ignore=E203,F401 src/ tests/

# Show statistics
flake8 --statistics src/ tests/
```

### Testing

#### Running Tests
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run specific test file
pytest tests/unit/test_search_engine.py

# Run specific test function
pytest tests/unit/test_search_engine.py::TestFileSearchEngine::test_initialization
```

#### Test Categories
```bash
# Unit tests only
pytest -m unit

# Integration tests only
pytest -m integration

# UI tests only
pytest -m ui

# Slow tests (exclude for quick testing)
pytest -m "not slow"
```

#### Coverage Reporting
```bash
# Generate coverage report
pytest --cov=filesearch --cov-report=html

# Generate coverage with terminal output
pytest --cov=filesearch --cov-report=term-missing

# Coverage with specific threshold
pytest --cov=filesearch --cov-fail-under=80
```

### Building and Packaging

#### Development Build
```bash
# Build package in development mode
python -m build

# Build wheel only
python -m build --wheel

# Build source distribution
python -m build --sdist
```

#### Production Build
```bash
# Install build dependencies
pip install build twine

# Build for distribution
python -m build

# Check package
twine check dist/*

# Upload to PyPI (test)
twine upload --repository testpypi dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## Architecture Overview

### Project Structure
```
src/filesearch/
├── core/               # Core business logic
│   ├── search_engine.py      # Multi-threaded search implementation
│   ├── config_manager.py     # Configuration management
│   ├── file_utils.py         # File operations utilities
│   ├── security_manager.py   # Security and permissions
│   └── sort_engine.py        # Result sorting algorithms
├── ui/                 # User interface components
│   ├── main_window.py        # Primary application window
│   ├── results_view.py       # Search results display
│   ├── search_controls.py     # Search input and controls
│   ├── sort_controls.py       # Results sorting interface
│   ├── settings_dialog.py     # Application settings
│   └── dialogs/              # Modal dialogs
├── plugins/            # Plugin system
│   ├── plugin_base.py        # Abstract plugin interface
│   ├── plugin_manager.py     # Plugin lifecycle management
│   └── builtin/              # Built-in plugins
├── models/             # Data models
│   └── search_result.py      # SearchResult dataclass
└── utils/              # Utility functions
    └── highlight_engine.py    # Text highlighting
```

### Key Components

#### Search Engine
- **Multi-threaded**: Parallel directory traversal
- **Generator-based**: Memory-efficient result streaming
- **Pattern Matching**: fnmatch patterns with regex support
- **Early Termination**: Stop when max results reached

#### Plugin System
- **Abstract Base**: `SearchPlugin` class for extension
- **Discovery**: Entry point and directory-based discovery
- **Lifecycle**: Initialize, search, cleanup management
- **Configuration**: Plugin-specific configuration support

#### UI Framework
- **PyQt6**: Cross-platform GUI framework
- **Model-View**: Custom models with Qt views
- **Signals/Slots**: Event-driven communication
- **Threading**: Background workers with progress indication

## Development Guidelines

### Code Style
- **Line Length**: 88 characters (Black default)
- **Import Style**: isort with Black profile
- **Type Hints**: Full type annotation coverage
- **Docstrings**: Google-style docstrings for all public functions

### Naming Conventions
- **Files**: `snake_case.py`
- **Classes**: `PascalCase`
- **Functions**: `snake_case`
- **Constants**: `UPPER_SNAKE_CASE`
- **Private**: `_leading_underscore`

### Error Handling
- **Custom Exceptions**: Use specific exception types from `filesearch.core.exceptions`
- **Logging**: Use loguru for structured logging
- **User Messages**: Provide clear, actionable error messages
- **Graceful Degradation**: Continue operation when possible

### Testing Guidelines
- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions
- **UI Tests**: Use pytest-qt for GUI testing
- **Coverage**: Maintain >80% test coverage

## Configuration

### Development Configuration
```python
# Development settings in config.json
{
    "search": {
        "max_results": 1000,
        "max_workers": 4,
        "case_sensitive": false,
        "use_regex": false
    },
    "ui": {
        "theme": "system",
        "window_size": [800, 600],
        "show_hidden": false
    },
    "logging": {
        "level": "DEBUG",
        "file_rotation": "5 MB",
        "retention": "10 days"
    }
}
```

### Environment Variables
```bash
# Override configuration
export FILESEARCH_LOG_LEVEL=DEBUG
export FILESEARCH_CONFIG_DIR=/path/to/config
export FILESEARCH_PLUGIN_DIR=/path/to/plugins
```

## Debugging

### Debug Mode
```bash
# Enable debug logging
python -m filesearch --debug

# Check log files
tail -f logs/filesearch.log
```

### Common Issues
- **Import Errors**: Ensure virtual environment is activated
- **PyQt6 Issues**: Install platform-specific Qt packages
- **Permission Errors**: Check file and directory permissions
- **Plugin Loading**: Verify plugin metadata and dependencies

### Performance Profiling
```bash
# Profile search performance
python -m cProfile -o profile.stats -m filesearch

# Analyze profile
python -c "
import pstats
p = pstats.Stats('profile.stats')
p.sort_stats('cumulative')
p.print_stats(20)
"
```

## Contributing

### Branch Strategy
- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/***: Feature development branches
- **bugfix/***: Bug fix branches

### Commit Process
1. Create feature branch from `develop`
2. Make changes with proper commit messages
3. Run tests and ensure they pass
4. Run code quality checks
5. Push branch and create pull request
6. Request code review

### Commit Message Format
```
type(scope): subject

body

footer
```

**Types**: feat, fix, docs, style, refactor, test, chore

**Example**:
```
feat(search): add fuzzy matching support

Implement fuzzy matching algorithm for search queries
to improve user experience when typos occur.

Closes #42
```

### Code Review Process
- **Automated Checks**: Pre-commit hooks must pass
- **Test Coverage**: New code must have tests
- **Documentation**: Update docs for new features
- **Performance**: Consider performance implications

## Plugin Development

### Creating a Plugin
```python
from filesearch.plugins.plugin_base import SearchPlugin

class MyPlugin(SearchPlugin):
    def __init__(self):
        super().__init__()
        self._name = "My Plugin"
        self._version = "1.0.0"

    def initialize(self, config):
        # Plugin initialization
        return True

    def search(self, query, context):
        # Search implementation
        results = []
        # ... search logic ...
        return results

    def cleanup(self):
        # Resource cleanup
        pass
```

### Plugin Metadata
```json
{
    "name": "My Plugin",
    "version": "1.0.0",
    "author": "Your Name",
    "description": "A custom search plugin",
    "dependencies": [],
    "min_app_version": "0.1.0"
}
```

## Troubleshooting

### Common Development Issues

#### PyQt6 Installation Issues
```bash
# Ubuntu/Debian
sudo apt-get install python3-pyqt6

# macOS
brew install pyqt6

# Windows
pip install PyQt6
```

#### Virtual Environment Issues
```bash
# Check if virtual environment is active
echo $VIRTUAL_ENV

# Deactivate and reactivate
deactivate
source venv/bin/activate
```

#### Test Issues
```bash
# Run specific test with output
pytest tests/unit/test_search_engine.py -v -s

# Run with debugging
pytest --pdb tests/unit/test_search_engine.py
```

### Getting Help
- **Documentation**: Check `docs/` directory for detailed guides
- **Issues**: Report bugs on GitHub Issues
- **Discussions**: Use GitHub Discussions for questions
- **Logs**: Check `logs/filesearch.log` for detailed error information
