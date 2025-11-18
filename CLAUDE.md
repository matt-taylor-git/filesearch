# CLAUDE.md - AI Assistant Development Guide

**Last Updated:** 2025-11-18
**Version:** 1.0.0

This document provides comprehensive guidance for AI assistants (like Claude) working with the File Search codebase. It covers architecture, conventions, workflows, and best practices to ensure consistent, high-quality contributions.

---

## Table of Contents

1. [Project Overview](#project-overview)
2. [Codebase Structure](#codebase-structure)
3. [Architecture & Design Patterns](#architecture--design-patterns)
4. [Development Workflow](#development-workflow)
5. [Code Quality Standards](#code-quality-standards)
6. [Testing Strategy](#testing-strategy)
7. [Key Components](#key-components)
8. [Common Patterns & Conventions](#common-patterns--conventions)
9. [Dependencies & Technology Stack](#dependencies--technology-stack)
10. [Git & CI/CD](#git--cicd)
11. [AI Assistant Guidelines](#ai-assistant-guidelines)
12. [Plugin Development](#plugin-development)
13. [Troubleshooting](#troubleshooting)

---

## Project Overview

**File Search** is a cross-platform desktop application built with Python and PyQt6 that provides fast, multi-threaded file and folder searching with an extensible plugin architecture.

### Key Features
- Fast file searching (sub-2-second target for typical directories)
- Cross-platform support (Windows, macOS, Linux)
- Extensible plugin architecture
- Modern PyQt6-based UI
- Advanced filtering and sorting
- Multi-threaded search with progress indication

### Project Metadata
- **Language:** Python 3.9+
- **GUI Framework:** PyQt6 (>=6.6.0)
- **Version:** 0.1.0 (Alpha)
- **License:** MIT
- **Repository Structure:** `src/` layout with clear module separation

### Success Criteria
- Search performance under 2 seconds for typical directory structures
- Cross-platform compatibility maintained
- Zero crashes during search operations
- Clean, maintainable, extensible codebase

---

## Codebase Structure

```
filesearch/
├── .bmad/                      # BMAD methodology files (project management)
├── .claude/                    # Claude Code slash commands
│   └── commands/              # Custom slash commands
├── .github/
│   └── workflows/
│       └── ci.yml             # CI/CD pipeline
├── .opencode/                 # OpenCode configuration
├── docs/                      # Documentation
│   ├── PRD.md                # Product Requirements Document
│   ├── architecture.md       # Architecture decisions
│   ├── epics.md              # Epic breakdown
│   ├── configuration.md      # Configuration guide
│   ├── plugin-development.md # Plugin development guide
│   ├── user_guide.md         # User documentation
│   └── sprint-artifacts/     # Sprint stories and artifacts
├── src/filesearch/           # Main application package
│   ├── __init__.py          # Package metadata and utilities
│   ├── main.py              # Application entry point
│   ├── core/                # Core business logic
│   │   ├── search_engine.py      # Multi-threaded search engine
│   │   ├── sort_engine.py        # Result sorting logic
│   │   ├── security_manager.py   # Security and permissions
│   │   ├── config_manager.py     # Configuration management
│   │   ├── config_schema.py      # Configuration schema
│   │   ├── file_utils.py         # File operations
│   │   └── exceptions.py         # Custom exception hierarchy
│   ├── ui/                  # User interface components
│   │   ├── main_window.py        # Main application window
│   │   ├── results_view.py       # Search results display
│   │   ├── settings_dialog.py    # Settings dialog
│   │   └── sort_controls.py      # Sort UI controls
│   ├── plugins/             # Plugin system
│   │   ├── plugin_base.py        # Abstract plugin base class
│   │   ├── plugin_manager.py     # Plugin lifecycle management
│   │   └── builtin/
│   │       └── example_plugin.py # Example plugin implementation
│   ├── models/              # Data models
│   │   └── search_result.py      # SearchResult dataclass
│   └── utils/               # Utility modules
│       └── highlight_engine.py    # Text highlighting utilities
├── tests/                   # Test suite
│   ├── unit/               # Unit tests
│   ├── integration/        # Integration tests
│   └── ui/                 # UI tests (pytest-qt)
├── scripts/                # Utility scripts
├── pyproject.toml         # Project configuration
├── requirements.txt       # Runtime dependencies
├── requirements-dev.txt   # Development dependencies
├── .pre-commit-config.yaml # Pre-commit hooks
├── .gitignore            # Git ignore patterns
└── README.md             # User-facing documentation
```

### Source Code Statistics
- **Source Files:** 21 Python modules
- **Test Files:** 19 test modules
- **Documentation:** 9 markdown files in docs/
- **Test Coverage Target:** >80%

---

## Architecture & Design Patterns

### Architectural Principles

1. **Separation of Concerns**
   - `core/`: Business logic, independent of UI
   - `ui/`: PyQt6 GUI components
   - `plugins/`: Extensibility layer
   - `models/`: Data structures

2. **Multi-threaded Design**
   - Search operations run in separate threads
   - PyQt signals/slots for thread-safe communication
   - Generator-based result streaming for memory efficiency

3. **Plugin Architecture**
   - Abstract base class (`SearchPlugin`)
   - Hybrid discovery (entry points + directory scanning)
   - Plugin manager handles lifecycle

4. **Configuration Management**
   - JSON-based configuration with platformdirs
   - Cross-platform config directory detection
   - Type-safe defaults with validation

### Design Patterns Used

- **MVC/Model-View Architecture** (PyQt6)
- **Strategy Pattern** (Plugin system)
- **Observer Pattern** (PyQt signals/slots)
- **Template Method** (SearchPlugin base class)
- **Singleton** (ConfigManager)
- **Factory** (Plugin loading)

### Core Architectural Decisions

| Decision | Rationale | Location |
|----------|-----------|----------|
| **PyQt6** | Native cross-platform UI, excellent threading | All UI components |
| **Multi-threading** | Meets <2s search requirement, UI responsiveness | `core/search_engine.py` |
| **Signals/Slots** | Thread-safe by design, clean separation | Throughout |
| **pathlib.Path** | Modern, cross-platform, type-safe | All file operations |
| **loguru** | Structured logging, rotation, thread-safe | Application-wide |
| **Dataclasses** | Type-safe models, self-documenting | `models/` |
| **pytest + pytest-qt** | Industry standard, handles Qt event loop | All tests |

---

## Development Workflow

### Initial Setup

```bash
# Clone repository
git clone https://github.com/filesearch/filesearch.git
cd filesearch

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/macOS:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Install pre-commit hooks
pre-commit install
```

### Development Commands

```bash
# Run application
python -m filesearch

# Run with debug logging
python -m filesearch --debug

# Run tests
pytest

# Run specific test types
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m ui           # UI tests only

# Run with coverage
pytest --cov=filesearch --cov-report=html

# Format code
black src/ tests/

# Check formatting (without modifying)
black --check src/ tests/

# Lint code
flake8 src/ tests/

# Check import sorting
isort --check-only --profile=black src/ tests/

# Fix import sorting
isort --profile=black src/ tests/

# Run all pre-commit hooks manually
pre-commit run --all-files
```

### Branch Strategy

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **bugfix/**: Bug fix branches
- **claude/**: AI assistant working branches

### Commit Conventions

Follow conventional commit format:
```
<type>(<scope>): <subject>

<body>

<footer>
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting)
- `refactor`: Code refactoring
- `test`: Test additions/changes
- `chore`: Build/tooling changes

**Example:**
```
feat(search): add fuzzy matching support

Implement fuzzy matching algorithm for search queries
to improve user experience when typos occur.

Closes #42
```

---

## Code Quality Standards

### Python Style Guide

**Line Length:** 88 characters (Black default)

**Formatting:** Black
```bash
black src/ tests/
```

**Import Sorting:** isort with Black profile
```python
# Standard library imports
import os
import sys
from pathlib import Path

# Third-party imports
from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

# Local imports
from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import SearchError
```

**Linting:** flake8
- Max line length: 88
- Ignore: E203 (whitespace before ':'), F401 (unused imports in `__init__.py`)
- Max complexity: 10

### Type Hints

**Always use type hints** for function signatures:

```python
def search_files(
    directory: Path,
    pattern: str,
    max_results: int = 1000
) -> Generator[SearchResult, None, None]:
    """Search for files matching pattern.

    Args:
        directory: Root directory to search
        pattern: fnmatch pattern to match
        max_results: Maximum number of results (0 = unlimited)

    Returns:
        Generator yielding SearchResult instances

    Raises:
        SearchError: If directory is invalid or inaccessible
    """
    pass
```

### Documentation Standards

**Module-level docstrings:**
```python
"""Module description.

This module provides [functionality]. It [key features].
"""
```

**Class docstrings:**
```python
class FileSearchEngine(QObject):
    """Multi-threaded file search engine with generator-based streaming.

    This class implements efficient file searching using concurrent directory
    traversal, partial matching with fnmatch patterns, and early termination.

    Attributes:
        max_workers (int): Maximum number of worker threads
        max_results (int): Maximum results to return (0 = unlimited)
        _cancelled (bool): Flag to indicate if search should be cancelled
    """
```

**Function docstrings:**
```python
def initialize(self, config: Dict[str, Any]) -> bool:
    """Initialize the plugin with configuration.

    Args:
        config: Configuration dictionary with plugin settings

    Returns:
        True if initialization succeeded, False otherwise

    Raises:
        PluginError: If required configuration is missing
    """
```

### Error Handling

**Use custom exception hierarchy:**

```python
from filesearch.core.exceptions import SearchError, ConfigError, PluginError

# Raise with context
raise SearchError(
    "Failed to access directory",
    path=str(directory),
    cause=e
)

# Catch and log
try:
    result = perform_search()
except SearchError as e:
    logger.error("Search failed: {} (path: {})", e.message, e.path)
    # Continue or re-raise as appropriate
```

**Exception hierarchy:**
- `FileSearchError` (base)
  - `SearchError` (search operations)
  - `PluginError` (plugin system)
  - `ConfigError` (configuration)
  - `UIError` (UI components)

### Logging

**Use loguru throughout:**

```python
from loguru import logger

# Different log levels
logger.debug("Detailed information for debugging")
logger.info("General information about operation")
logger.warning("Warning about potential issue")
logger.error("Error occurred but recoverable")
logger.exception("Error with full traceback")

# Structured logging with context
logger.info(
    "Search completed: {} results in {:.2f}s",
    result_count,
    elapsed_time
)
```

**Log levels:**
- `DEBUG`: Detailed diagnostic information
- `INFO`: General operational information
- `WARNING`: Potential issues, degraded functionality
- `ERROR`: Errors that are recoverable
- `CRITICAL`: Unrecoverable errors

---

## Testing Strategy

### Test Structure

```
tests/
├── unit/                    # Fast, isolated unit tests
│   ├── test_search_engine.py
│   ├── test_config_manager.py
│   ├── test_plugin_manager.py
│   └── ...
├── integration/             # Multi-component integration tests
│   ├── test_search_performance.py
│   ├── test_plugin_system.py
│   └── ...
└── ui/                      # GUI tests with pytest-qt
    ├── test_main_window.py
    ├── test_results_view.py
    └── ...
```

### Test Markers

```python
import pytest

@pytest.mark.unit
def test_search_engine_initialization():
    """Unit test for search engine."""
    pass

@pytest.mark.integration
def test_full_search_workflow():
    """Integration test for complete search."""
    pass

@pytest.mark.ui
def test_main_window_display(qtbot):
    """UI test with pytest-qt."""
    pass

@pytest.mark.slow
def test_large_directory_search():
    """Slow running test."""
    pass
```

### Writing Tests

**Unit test example:**
```python
import pytest
from pathlib import Path
from filesearch.core.search_engine import FileSearchEngine
from filesearch.core.exceptions import SearchError

class TestFileSearchEngine:
    def test_initialization(self):
        """Test search engine initializes with defaults."""
        engine = FileSearchEngine()
        assert engine.max_workers > 0
        assert engine.max_results == 1000

    def test_invalid_directory_raises_error(self):
        """Test that invalid directory raises SearchError."""
        engine = FileSearchEngine()
        with pytest.raises(SearchError):
            list(engine.search(Path("/nonexistent"), "*.txt"))
```

**UI test example:**
```python
import pytest
from PyQt6.QtCore import Qt
from filesearch.ui.main_window import MainWindow

@pytest.mark.ui
def test_search_button_click(qtbot, mocker):
    """Test search button triggers search."""
    window = MainWindow()
    qtbot.addWidget(window)

    # Mock search
    mock_search = mocker.patch.object(window, '_perform_search')

    # Click search button
    qtbot.mouseClick(window.search_button, Qt.LeftButton)

    # Verify search was triggered
    mock_search.assert_called_once()
```

### Coverage Requirements

- **Overall:** >80%
- **Core modules:** >90%
- **UI modules:** >70%
- **Plugins:** >80%

Run coverage report:
```bash
pytest --cov=filesearch --cov-report=html --cov-report=term-missing
```

---

## Key Components

### 1. Search Engine (`core/search_engine.py`)

**Purpose:** Multi-threaded file search with generator-based streaming

**Key Methods:**
- `search(directory, pattern, **kwargs)`: Main search method
- `cancel()`: Cancel ongoing search
- `_search_directory(directory, pattern)`: Worker method for single directory

**Threading Model:**
- Uses `ThreadPoolExecutor` for parallel directory traversal
- Emits PyQt signals for progress updates
- Generator-based to avoid loading all results in memory

**Usage:**
```python
engine = FileSearchEngine(max_workers=4, max_results=1000)
for result in engine.search(Path("/home/user"), "*.py"):
    print(result.path)
```

### 2. Configuration Manager (`core/config_manager.py`)

**Purpose:** Cross-platform configuration management

**Key Methods:**
- `get(key, default=None)`: Get configuration value
- `set(key, value)`: Set configuration value
- `save()`: Persist configuration to disk
- `load()`: Load configuration from disk

**Configuration File:** `~/.config/filesearch/config.json` (Linux/macOS) or `%APPDATA%\filesearch\config.json` (Windows)

**Usage:**
```python
config = ConfigManager()
max_results = config.get("search.max_results", 1000)
config.set("ui.theme", "dark")
config.save()
```

### 3. Plugin System (`plugins/`)

**Purpose:** Extensible architecture for custom search providers

**Key Classes:**
- `SearchPlugin`: Abstract base class for all plugins
- `PluginManager`: Discovers, loads, and manages plugins

**Plugin Lifecycle:**
1. Discovery (entry points or directory scan)
2. Loading (import and instantiation)
3. Initialization (with config)
4. Execution (search methods)
5. Cleanup (resource disposal)

**Creating a Plugin:**
```python
from filesearch.plugins.plugin_base import SearchPlugin

class MyPlugin(SearchPlugin):
    def initialize(self, config):
        self.api_key = config.get("my_plugin.api_key")
        return True

    def search(self, query, context):
        results = []
        # Implement search logic
        return results
```

### 4. Search Result Model (`models/search_result.py`)

**Purpose:** Immutable data structure for search results

**Structure:**
```python
@dataclass
class SearchResult:
    path: Path              # File/folder path
    size: int              # Size in bytes (0 for directories)
    modified: float        # Modification timestamp
    plugin_source: Optional[str] = None  # Plugin that provided result
```

**Display Methods:**
- `get_display_name()`: Filename for display
- `get_display_path()`: Path with home directory abbreviated
- `get_display_size()`: Human-readable size (B, KiB, MiB, etc.)
- `get_display_date()`: Formatted modification date

### 5. Main Window (`ui/main_window.py`)

**Purpose:** Main application GUI

**Components:**
- Search input field
- Directory selector
- Search button
- Results view
- Status bar
- Menu bar with settings

**Threading:**
- Search operations run in `QThread`
- Results streamed back via signals
- UI remains responsive during search

### 6. Exception Hierarchy (`core/exceptions.py`)

**Purpose:** Type-safe error handling with context

**Classes:**
- `FileSearchError`: Base exception
- `SearchError`: Search operation failures
- `PluginError`: Plugin system errors
- `ConfigError`: Configuration errors
- `UIError`: UI component errors

**Usage:**
```python
raise SearchError(
    "Permission denied accessing directory",
    path=str(directory),
    details={"permissions": oct(path.stat().st_mode)},
    cause=original_exception
)
```

---

## Common Patterns & Conventions

### 1. Path Handling

**Always use pathlib.Path:**
```python
from pathlib import Path

# Good
directory = Path.home() / "Documents"
if directory.exists() and directory.is_dir():
    for file in directory.iterdir():
        process(file)

# Avoid
import os
directory = os.path.expanduser("~/Documents")
if os.path.exists(directory) and os.path.isdir(directory):
    for file in os.listdir(directory):
        process(os.path.join(directory, file))
```

### 2. PyQt Signal/Slot Pattern

**Define signals at class level:**
```python
from PyQt6.QtCore import QObject, pyqtSignal

class SearchWorker(QObject):
    # Define signals
    result_found = pyqtSignal(object)  # SearchResult
    search_complete = pyqtSignal(int)  # result_count
    error_occurred = pyqtSignal(str)   # error_message

    def search(self):
        try:
            for result in self.engine.search(self.directory, self.pattern):
                self.result_found.emit(result)
            self.search_complete.emit(self.result_count)
        except Exception as e:
            self.error_occurred.emit(str(e))
```

**Connect signals to slots:**
```python
worker = SearchWorker(engine, directory, pattern)
worker.result_found.connect(self.add_result)
worker.search_complete.connect(self.show_completion)
worker.error_occurred.connect(self.show_error)
```

### 3. Generator Pattern for Streaming

**Use generators for large result sets:**
```python
def search_directory(
    directory: Path,
    pattern: str
) -> Generator[SearchResult, None, None]:
    """Search directory yielding results as found."""
    for entry in directory.rglob(pattern):
        if self._cancelled:
            break
        yield SearchResult(
            path=entry,
            size=entry.stat().st_size if entry.is_file() else 0,
            modified=entry.stat().st_mtime
        )
```

### 4. Configuration Pattern

**Default values in code, override from config:**
```python
class SearchEngine:
    def __init__(self, config_manager=None):
        # Get from config or use default
        self.max_workers = (
            config_manager.get("search.max_workers", 4)
            if config_manager
            else 4
        )
        self.max_results = (
            config_manager.get("search.max_results", 1000)
            if config_manager
            else 1000
        )
```

### 5. Error Recovery Pattern

**Continue on error, log for debugging:**
```python
results = []
for directory in directories:
    try:
        results.extend(search_directory(directory))
    except PermissionError as e:
        logger.warning("Permission denied: {}", directory)
        # Continue with other directories
    except Exception as e:
        logger.error("Unexpected error searching {}: {}", directory, e)
        # Continue with other directories

return results
```

### 6. Resource Cleanup Pattern

**Use context managers and cleanup methods:**
```python
class SearchEngine(QObject):
    def __init__(self):
        self._executor = None

    def search(self, directory, pattern):
        try:
            self._executor = ThreadPoolExecutor(max_workers=self.max_workers)
            # Perform search
        finally:
            self.cleanup()

    def cleanup(self):
        """Clean up resources."""
        if self._executor:
            self._executor.shutdown(wait=False)
            self._executor = None
```

---

## Dependencies & Technology Stack

### Runtime Dependencies

```
PyQt6>=6.6.0          # GUI framework
loguru>=0.7.2         # Structured logging
platformdirs>=4.0.0   # Cross-platform directories
natsort               # Natural sorting of results
```

### Development Dependencies

```
pytest>=7.4.0         # Testing framework
pytest-qt>=4.2.0      # Qt testing support
black>=23.0.0         # Code formatting
flake8>=6.0.0         # Linting
pre-commit>=3.0.0     # Pre-commit hooks
psutil>=5.9.0         # System utilities (testing)
natsort               # Natural sorting
```

### Python Version

**Required:** Python 3.9 or higher

**Tested:** 3.9, 3.10, 3.11, 3.12

**Type hints:** Uses modern Python 3.9+ features

### Key Libraries

**PyQt6:**
- `QMainWindow`, `QWidget`: UI components
- `QThread`, `QThreadPool`: Threading
- `QObject`, `pyqtSignal`: Signals/slots
- `QListWidget`, `QListView`: Results display

**loguru:**
- Structured logging with automatic rotation
- Context variables for request tracking
- Thread-safe logging

**platformdirs:**
- Cross-platform directory detection
- Config: `~/.config/filesearch/` (Linux), `~/Library/Application Support/filesearch/` (macOS), `%APPDATA%\filesearch\` (Windows)

---

## Git & CI/CD

### Git Configuration

**.gitignore highlights:**
- Python artifacts: `__pycache__/`, `*.pyc`, `*.pyo`
- Virtual environments: `venv/`, `.venv/`
- IDE: `.vscode/`, `.idea/`
- Logs: `logs/`, `*.log`
- Test coverage: `.coverage`, `htmlcov/`
- OS files: `.DS_Store`, `Thumbs.db`

### Pre-commit Hooks

**Hooks configured (`.pre-commit-config.yaml`):**
1. **trailing-whitespace**: Remove trailing whitespace
2. **end-of-file-fixer**: Ensure files end with newline
3. **check-yaml**: Validate YAML syntax
4. **check-added-large-files**: Prevent large file commits
5. **check-merge-conflict**: Detect merge conflict markers
6. **debug-statements**: Detect debug print statements
7. **black**: Code formatting
8. **flake8**: Linting
9. **isort**: Import sorting

**Manual run:**
```bash
pre-commit run --all-files
```

### CI/CD Pipeline (`.github/workflows/ci.yml`)

**Triggers:**
- Push to `main` or `develop`
- Pull requests to `main` or `develop`

**Jobs:**

**1. Test Job (Matrix):**
- **OS:** ubuntu-latest, windows-latest, macos-latest
- **Python:** 3.9, 3.10, 3.11, 3.12
- **Steps:**
  1. Checkout code
  2. Set up Python
  3. Install dependencies
  4. Lint with flake8
  5. Check formatting (black)
  6. Check imports (isort)
  7. Run tests with coverage
  8. Upload coverage to Codecov

**2. Build Job:**
- **Runs on:** ubuntu-latest
- **Python:** 3.11
- **Steps:**
  1. Checkout code
  2. Set up Python
  3. Install build tools
  4. Build package
  5. Upload artifacts

### Release Process

1. Update version in `pyproject.toml` and `src/filesearch/__init__.py`
2. Update `CHANGELOG.md` (if exists)
3. Create release branch: `release/v0.1.0`
4. Merge to `main` via PR
5. Tag release: `git tag -a v0.1.0 -m "Release v0.1.0"`
6. Push tag: `git push origin v0.1.0`
7. GitHub Actions builds and publishes release

---

## AI Assistant Guidelines

### Understanding Context

**Before making changes:**

1. **Read relevant documentation:**
   - `docs/PRD.md` - Product requirements
   - `docs/architecture.md` - Architecture decisions
   - `docs/epics.md` - Feature breakdown
   - This file (CLAUDE.md) - Development guide

2. **Understand the component:**
   - Read the module you're modifying
   - Check related tests
   - Review usage in other modules

3. **Check existing patterns:**
   - Look for similar implementations
   - Follow established conventions
   - Maintain consistency

### Making Changes

**When implementing features:**

1. **Start with tests:**
   ```python
   # Write test first
   def test_new_feature():
       result = new_feature(input_data)
       assert result == expected_output
   ```

2. **Implement in small steps:**
   - One logical change at a time
   - Commit frequently with clear messages
   - Run tests after each change

3. **Follow the architecture:**
   - Core logic in `core/`
   - UI code in `ui/`
   - Models in `models/`
   - Plugins in `plugins/`

4. **Add documentation:**
   - Module docstrings
   - Class docstrings
   - Function docstrings with types
   - Inline comments for complex logic

5. **Handle errors gracefully:**
   ```python
   try:
       result = risky_operation()
   except SpecificError as e:
       logger.error("Operation failed: {}", e)
       raise CustomError("User-friendly message", cause=e)
   ```

### Code Review Checklist

Before submitting changes, verify:

- [ ] **Functionality:** Code works as intended
- [ ] **Tests:** New tests added, existing tests pass
- [ ] **Documentation:** Docstrings and comments added
- [ ] **Type hints:** All functions have type hints
- [ ] **Error handling:** Exceptions caught and logged
- [ ] **Logging:** Appropriate log statements added
- [ ] **Formatting:** Black, flake8, isort pass
- [ ] **No regressions:** Existing functionality unchanged
- [ ] **Cross-platform:** Works on Windows, macOS, Linux
- [ ] **Thread-safe:** No race conditions or deadlocks
- [ ] **Performance:** No performance degradation

### Common Pitfalls to Avoid

1. **Don't block the UI thread:**
   ```python
   # Bad
   def search_button_clicked(self):
       results = self.engine.search(directory, pattern)  # Blocks UI!

   # Good
   def search_button_clicked(self):
       self.worker = SearchWorker(self.engine, directory, pattern)
       self.worker.result_found.connect(self.add_result)
       self.worker.start()  # Runs in separate thread
   ```

2. **Don't use string paths:**
   ```python
   # Bad
   path = "/home/user/file.txt"
   if os.path.exists(path):
       ...

   # Good
   path = Path("/home/user/file.txt")
   if path.exists():
       ...
   ```

3. **Don't swallow exceptions:**
   ```python
   # Bad
   try:
       risky_operation()
   except Exception:
       pass  # Silently fails!

   # Good
   try:
       risky_operation()
   except SpecificError as e:
       logger.error("Operation failed: {}", e)
       # Re-raise or handle appropriately
   ```

4. **Don't forget cleanup:**
   ```python
   # Bad
   def search(self):
       self.executor = ThreadPoolExecutor()
       # No cleanup!

   # Good
   def search(self):
       try:
           self.executor = ThreadPoolExecutor()
           # Perform search
       finally:
           if self.executor:
               self.executor.shutdown(wait=False)
   ```

5. **Don't ignore cross-platform differences:**
   ```python
   # Bad
   path = "/home/user/file.txt"  # Unix-only

   # Good
   path = Path.home() / "file.txt"  # Cross-platform
   ```

### Interacting with User

**When asking questions:**
- Be specific about what you need to know
- Explain why you need the information
- Provide context about the decision

**When reporting issues:**
- Describe what you found
- Explain the impact
- Suggest solutions or alternatives
- Ask for guidance if uncertain

**When suggesting improvements:**
- Explain the current behavior
- Describe the proposed change
- Outline benefits and trade-offs
- Request approval before implementing

---

## Plugin Development

### Plugin Structure

**Minimum plugin implementation:**

```python
from filesearch.plugins.plugin_base import SearchPlugin
from typing import Dict, List, Any

class ExamplePlugin(SearchPlugin):
    """Example plugin demonstrating the plugin API."""

    def __init__(self, metadata=None):
        """Initialize plugin with metadata."""
        super().__init__(metadata)
        self._name = "Example Plugin"
        self._version = "1.0.0"
        self._author = "Your Name"
        self._description = "An example plugin"

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize plugin with configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if initialization succeeded
        """
        # Perform initialization
        self._enabled = True
        return True

    def search(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform search based on query.

        Args:
            query: Search query string
            context: Search context (directory, max_results, etc.)

        Returns:
            List of result dictionaries
        """
        results = []
        # Implement search logic
        return results

    def cleanup(self) -> None:
        """Clean up plugin resources."""
        # Release resources
        pass
```

### Plugin Metadata

**Create `plugin.json` in plugin directory:**

```json
{
  "name": "Example Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "An example plugin for File Search",
  "dependencies": [],
  "min_app_version": "0.1.0",
  "max_app_version": "1.0.0",
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "API key for service",
      "required": false
    },
    "max_results": {
      "type": "integer",
      "description": "Maximum results to return",
      "default": 100
    }
  }
}
```

### Plugin Installation

**Option 1: Directory installation**
```bash
mkdir -p ~/.filesearch/plugins/my_plugin
cp my_plugin.py ~/.filesearch/plugins/my_plugin/
cp plugin.json ~/.filesearch/plugins/my_plugin/
```

**Option 2: Entry point installation**
```python
# setup.py
setup(
    name="my-plugin",
    version="1.0.0",
    py_modules=["my_plugin"],
    entry_points={
        "filesearch.plugins": [
            "my_plugin = my_plugin:MyPlugin",
        ],
    },
)
```

### Plugin Testing

**Create tests in `tests/unit/test_my_plugin.py`:**

```python
import pytest
from my_plugin import MyPlugin

class TestMyPlugin:
    def test_initialization(self):
        """Test plugin initializes correctly."""
        plugin = MyPlugin()
        assert plugin.initialize({}) is True
        assert plugin._enabled is True

    def test_search_returns_results(self):
        """Test plugin search returns expected results."""
        plugin = MyPlugin()
        plugin.initialize({})

        results = plugin.search("test", {"directory": "/tmp"})
        assert isinstance(results, list)
```

### Plugin Best Practices

1. **Error handling:**
   ```python
   def search(self, query, context):
       try:
           return self._perform_search(query, context)
       except Exception as e:
           logger.error("Plugin {} failed: {}", self._name, e)
           return []  # Return empty results on error
   ```

2. **Respect max_results:**
   ```python
   def search(self, query, context):
       max_results = context.get("max_results", 1000)
       results = []
       for result in self._search_generator(query):
           if len(results) >= max_results:
               break
           results.append(result)
       return results
   ```

3. **Use plugin logger:**
   ```python
   from loguru import logger

   logger.info("Plugin {} starting search", self._name)
   ```

4. **Clean up resources:**
   ```python
   def cleanup(self):
       """Clean up plugin resources."""
       if hasattr(self, '_connection'):
           self._connection.close()
       if hasattr(self, '_cache'):
           self._cache.clear()
   ```

---

## Troubleshooting

### Common Issues

**1. Import errors:**
```
ModuleNotFoundError: No module named 'PyQt6'
```
**Solution:** Install dependencies
```bash
pip install -r requirements.txt
```

**2. Qt platform plugin error:**
```
qt.qpa.plugin: Could not load the Qt platform plugin "xcb"
```
**Solution:** Install Qt dependencies (Linux)
```bash
sudo apt-get install libxcb-xinerama0
```

**3. Permission errors during search:**
```
PermissionError: [Errno 13] Permission denied
```
**Solution:** This is expected. The search engine logs and continues with other directories.

**4. Tests fail with Qt errors:**
```
QWidget: Must construct a QApplication before a QWidget
```
**Solution:** Use pytest-qt fixtures
```python
@pytest.mark.ui
def test_ui_component(qtbot):
    widget = MyWidget()
    qtbot.addWidget(widget)
```

**5. Pre-commit hooks fail:**
```
black....................................Failed
```
**Solution:** Run black to format code
```bash
black src/ tests/
```

### Debugging

**Enable debug logging:**
```bash
python -m filesearch --debug
```

**Check log files:**
```
# Linux/macOS
~/.local/share/filesearch/logs/

# Windows
%APPDATA%\filesearch\logs\
```

**Run specific test with verbose output:**
```bash
pytest tests/unit/test_search_engine.py::test_specific_test -vv
```

**Profile search performance:**
```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()
# Run search
profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats()
```

### Getting Help

1. **Check documentation:**
   - This file (CLAUDE.md)
   - `docs/architecture.md`
   - `docs/user_guide.md`

2. **Search existing issues:**
   - GitHub issue tracker

3. **Ask in discussions:**
   - GitHub discussions

4. **Review test cases:**
   - `tests/` directory for examples

---

## Appendix

### Useful Commands Reference

```bash
# Development
python -m filesearch --debug        # Run with debug logging
pytest -v                           # Verbose test output
pytest --lf                         # Run last failed tests
pytest --pdb                        # Drop into debugger on failure

# Code quality
black --diff src/                   # Show what black would change
flake8 --statistics src/            # Show linting statistics
isort --diff src/                   # Show import sort changes

# Performance
pytest --durations=10               # Show 10 slowest tests
pytest -m "not slow"                # Skip slow tests

# Coverage
pytest --cov=filesearch --cov-report=html
pytest --cov=filesearch --cov-report=term-missing

# Build
python -m build                     # Build distribution packages
pip install -e .                    # Install in editable mode
```

### File Locations by Platform

| Resource | Linux | macOS | Windows |
|----------|-------|-------|---------|
| Config | `~/.config/filesearch/` | `~/Library/Application Support/filesearch/` | `%APPDATA%\filesearch\` |
| Logs | `~/.local/share/filesearch/logs/` | `~/Library/Logs/filesearch/` | `%APPDATA%\filesearch\logs\` |
| Plugins | `~/.filesearch/plugins/` | `~/.filesearch/plugins/` | `%USERPROFILE%\.filesearch\plugins\` |

### Related Documentation

- **README.md** - User-facing project overview
- **docs/PRD.md** - Product Requirements Document
- **docs/architecture.md** - Detailed architecture decisions
- **docs/epics.md** - Feature breakdown and epics
- **docs/user_guide.md** - End-user documentation
- **docs/plugin-development.md** - Plugin development guide
- **docs/configuration.md** - Configuration options

---

**Document Maintenance:**
- Review and update after major changes
- Keep examples current with codebase
- Add new sections as needed
- Remove deprecated information

**Last reviewed:** 2025-11-18
**Next review:** After v0.2.0 release
