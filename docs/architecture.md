# File Search - Architecture

## Executive Summary

File Search is a cross-platform desktop application built with PyQt6 that provides fast, multi-threaded file and folder search with an extensible plugin architecture. The architecture emphasizes performance (sub-2-second searches), user experience (native platform integration), and extensibility (plugin system for future features like folder visualization).

The application follows a modular architecture with clear separation between UI components (PyQt6), core business logic (search engine, file utilities), and extensibility layer (plugin system). Multi-threading ensures UI responsiveness during searches, while QSettings provides cross-platform configuration management.

## Project Initialization

First implementation story should execute:

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or venv\Scripts\activate  # Windows

# Install dependencies
pip install PyQt6 loguru pytest pytest-qt

# Create project structure
mkdir -p src/filesearch/{core,ui,plugins/{builtin},models,utils}
mkdir -p tests/{unit,integration,ui}
mkdir -p docs
mkdir -p scripts

# Create initial files
touch src/filesearch/__init__.py src/filesearch/main.py
```

This establishes the base architecture with these decisions provided by the starter:
- **GUI Framework**: PyQt6 for cross-platform native UI
- **Language**: Python 3.9+ with type hints
- **Logging**: loguru for modern structured logging
- **Testing**: pytest with pytest-qt for Qt testing
- **Project Structure**: src/ layout with clear module separation

## Decision Summary

| Category | Decision | Version | Affects Epics | Rationale |
| -------- | -------- | ------- | ------------- | --------- |
| GUI Framework | PyQt6 | 6.6.0 | All | Native cross-platform UI, excellent threading support, professional appearance |
| Search Implementation | Multi-threaded with concurrent.futures | Python 3.9+ | Epic 2, 3 | Meets <2s requirement, scales to 100K files, keeps UI responsive |
| Threading Model | PyQt Signals/Slots | PyQt6 | Epic 2, 3 | Thread-safe by design, native Qt approach, clean separation |
| Plugin Architecture | Hybrid (Entry Points + Directory) | Custom | Epic 1, 3 | Maximum flexibility for distributed and user-developed plugins |
| Configuration Storage | QSettings | PyQt6 | Epic 1, 2 | Cross-platform automatic storage, type-safe, no file format decisions |
| Error Handling | Custom Exception Hierarchy | Custom | All | Clean API, user-friendly messages, easy to add error codes for i18n |
| Logging | loguru | 0.7.2 | All | Modern API, automatic rotation/retention, structured logging, thread-safe |
| Testing | pytest with pytest-qt | pytest 7.4+, pytest-qt 4.2+ | All | Industry standard, pytest-qt handles Qt event loop automatically |
| File System | pathlib.Path | Python 3.9+ | All | Modern, object-oriented, cross-platform, type-safe |
| Error Recovery | Continue with logging | Custom | Epic 2, 3 | Users want results even with permission errors, loguru captures for debugging |
| Date/Time Format | Store timestamp, display local | Custom | Epic 3 | Efficient storage, user-friendly display, respects OS locale |
| API Response Format | Dataclass | Python 3.9+ | All | Type-safe, can add methods, easy serialization, self-documenting |

## Project Structure

```
filesearch/
├── pyproject.toml                 # Modern Python packaging
├── requirements.txt               # Runtime dependencies (PyQt6, loguru)
├── requirements-dev.txt           # Dev dependencies (pytest, pytest-qt, black, flake8)
├── README.md                      # Project overview
├── LICENSE                        # MIT or GPL (depending on PyQt6 licensing choice)
│
├── src/
│   └── filesearch/
│       ├── __init__.py           # Package version
│       ├── main.py               # Application entry point
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── search_engine.py      # Multi-threaded search with os.scandir()
│       │   ├── file_utils.py         # File operations (open, folder navigation)
│       │   ├── config_manager.py     # QSettings wrapper
│       │   └── exceptions.py         # Custom exception hierarchy
│       │
│       ├── ui/
│       │   ├── __init__.py
│       │   ├── main_window.py        # Main GUI window (QMainWindow)
│       │   ├── search_controls.py    # Search input, directory selector, buttons
│       │   ├── results_view.py       # QListView with custom model
│       │   ├── progress_widget.py    # QProgressBar and status labels
│       │   └── settings_dialog.py    # Configuration dialog
│       │
│       ├── plugins/
│       │   ├── __init__.py
│       │   ├── plugin_base.py        # Abstract base class SearchPlugin
│       │   ├── plugin_manager.py     # Plugin discovery and loading
│       │   └── builtin/
│       │       ├── __init__.py
│       │       └── example_plugin.py # Template plugin implementation
│       │
│       ├── models/
│       │   ├── __init__.py
│       │   └── search_result.py      # SearchResult dataclass
│       │
│       └── utils/
│           ├── __init__.py
│           ├── logger.py             # loguru configuration
│           └── path_helpers.py       # pathlib.Path utilities
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py              # pytest fixtures (qapp, qtbot)
│   ├── unit/
│   │   ├── test_search_engine.py
│   │   ├── test_config_manager.py
│   │   └── test_plugin_manager.py
│   ├── integration/
│   │   ├── test_search_workflow.py
│   │   └── test_plugin_system.py
│   └── ui/
│       ├── test_main_window.py
│       └── test_results_view.py
│
├── docs/
│   ├── architecture.md          # This document
│   ├── user_guide.md            # User documentation
│   ├── plugin_development.md    # Plugin API guide
│   └── configuration.md         # Configuration options
│
├── scripts/
│   ├── setup_dev.sh             # Development setup (Linux/Mac)
│   ├── setup_dev.bat            # Development setup (Windows)
│   └── build_executable.py      # PyInstaller build script
│
├── examples/
│   └── plugins/
│       └── custom_search.py     # Example custom plugin
│
└── logs/                        # Created at runtime
    └── filesearch.log           # Rotating log files
```

## Epic to Architecture Mapping

| Epic | Module | Story | Description |
|------|--------|-------|-------------|
| **Epic 1: Extensibility Foundation** | | | |
| | `core/config_manager.py` | 1.3 | QSettings wrapper for cross-platform config |
| | `core/exceptions.py` | 1.2 | Custom exception hierarchy |
| | `plugins/plugin_base.py` | 1.4 | Abstract SearchPlugin base class |
| | `plugins/plugin_manager.py` | 1.4 | Plugin discovery and lifecycle management |
| | `models/search_result.py` | 1.2 | Universal result format |
| | `utils/logger.py` | 1.1 | loguru configuration |
| **Epic 2: Search Interface** | | | |
| | `core/search_engine.py` | 2.1 | Multi-threaded search with os.scandir() |
| | `ui/search_controls.py` | 2.2, 2.3, 2.4 | Search input, directory selector, buttons |
| | `ui/progress_widget.py` | 2.5 | QProgressBar and status labels |
| | `ui/main_window.py` | 2.6 | Main window with status display |
| **Epic 3: Results Management** | | | |
| | `ui/results_view.py` | 3.1, 3.2, 3.3 | QListView with virtual scrolling, highlighting, sorting |
| | `core/file_utils.py` | 3.4, 3.6 | File opening and folder navigation |
| | `ui/main_window.py` | 3.5 | Context menu implementation |

## Technology Stack Details

### Core Technologies

**PyQt6 (6.6.0)**
- Cross-platform GUI framework with native look and feel
- Provides: QMainWindow, QListView, QThread, QSettings, QFileDialog, QProgressBar, QMenu
- License: GPL or Commercial (choose based on distribution model)
- Installation: `pip install PyQt6`

**loguru (0.7.2)**
- Modern structured logging with automatic rotation and retention
- Features: Colored console output, file rotation (5MB), retention (10 days), compression
- Thread-safe by design, excellent performance
- Installation: `pip install loguru`

**pytest (7.4+)**
- Testing framework with fixtures, parametrization, and plugins
- **pytest-qt (4.2+)**: Qt-specific testing utilities, event loop management, widget cleanup
- Installation: `pip install pytest pytest-qt`

**Python Standard Library**
- `pathlib.Path`: Object-oriented file system paths (Python 3.9+)
- `concurrent.futures`: Thread pool management for multi-threaded search
- `os`, `sys`: System integration and file operations
- `datetime`: Date/time handling for file timestamps

### Integration Points

**UI → Core Communication:**
- MainWindow creates SearchEngine instance
- SearchEngine moved to QThread for background execution
- Signal connections (thread-safe):
  - `SearchEngine.result_found → MainWindow.on_result_found`
  - `SearchEngine.progress_update → MainWindow.on_progress_update`
  - `SearchEngine.search_complete → MainWindow.on_search_complete`
  - `SearchEngine.error_occurred → MainWindow.on_error_occurred`

**Core → Plugin Communication:**
- PluginManager discovers plugins via entry_points and directory scanning
- Plugins inherit from SearchPlugin abstract base class
- Plugin lifecycle: discovery → load → initialize → enable/disable → unload
- Plugin.search() returns List[SearchResult] dataclass
- Error isolation: plugin failures logged but don't crash main application

**Configuration Flow:**
- ConfigManager wraps QSettings with organization="Matt", application="FileSearch"
- Config paths (automatically handled by Qt):
  - Windows: `HKEY_CURRENT_USER\Software\Matt\FileSearch`
  - macOS: `~/Library/Preferences/com.matt.FileSearch.plist`
  - Linux: `~/.config/Matt/FileSearch.conf`
- Settings cached in memory for performance, saved immediately on change

**Logging Flow:**
- loguru configured in `utils/logger.py` with rotation, retention, compression
- Logger imported and used throughout all modules
- Structured logging: `logger.bind(search_id=123).debug("Found file: {}", filepath)`
- Separate log levels: DEBUG (development), INFO (production), WARNING/ERROR (issues)

## Implementation Patterns

These patterns ensure consistent implementation across all AI agents:

### Naming Conventions

**File Naming:**
- Python modules: `snake_case.py` (e.g., `search_engine.py`, `main_window.py`)
- Plugin files: `*_plugin.py` (e.g., `example_plugin.py`, `recent_files_plugin.py`)
- Test files: `test_*.py` (e.g., `test_search_engine.py`)
- UI files: `*_view.py`, `*_dialog.py`, `*_widget.py` (e.g., `results_view.py`, `settings_dialog.py`)

**Class Naming:**
- Business logic: `PascalCase` descriptive names (e.g., `SearchEngine`, `ConfigManager`)
- UI classes: `PascalCase` with suffix (e.g., `MainWindow`, `SearchControls`, `ResultsView`)
- Base/Abstract classes: `PascalCase` with `Base` or `Abstract` suffix (e.g., `SearchPluginBase`)
- Exception classes: `PascalCase` with `Error` suffix (e.g., `SearchError`, `PluginError`)

**Function/Method Naming:**
- Public methods: `snake_case` descriptive verbs (e.g., `search()`, `get_results()`, `load_config()`)
- Private methods: `snake_case` with leading underscore (e.g., `_scan_directory()`, `_validate_query()`)
- Signal handlers: `on_event_name` (e.g., `on_search_clicked()`, `on_result_found()`)
- Qt slot methods: `handle_event_name` (e.g., `handle_search_complete()`)

**Variable Naming:**
- Instance variables: `snake_case` (e.g., `self.search_thread`, `self.results_model`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_RESULTS`, `DEFAULT_TIMEOUT`)
- Type hints: Use for all public methods and attributes

### Code Organization

**Module Structure:**
```python
# Each module follows this structure:
# 1. Imports (stdlib first, then third-party, then local)
# 2. Constants
# 3. Type definitions (TypeAlias, dataclasses)
# 4. Exception definitions
# 5. Class definitions (public first, then private)
# 6. Function definitions (public first, then private)
# 7. if __name__ == "__main__":  # Only in entry points
```

**Class Structure:**
```python
class ClassName:
    """Docstring with description and attributes"""

    # Class variables
    CLASS_CONSTANT = value

    def __init__(self, param1: Type, param2: Type = default):
        """Initialize with parameters"""
        self.instance_var = param1  # Public
        self._private_var = param2  # Private

    def public_method(self, arg: Type) -> ReturnType:
        """Public method docstring"""
        return result

    def _private_method(self, arg: Type) -> ReturnType:
        """Private method docstring"""
        return result
```

**Plugin Structure:**
```python
# All plugins must follow this exact structure
from filesearch.plugins.plugin_base import SearchPlugin
from filesearch.models.search_result import SearchResult

class MyPlugin(SearchPlugin):
    def initialize(self, config: Dict) -> bool:
        # Initialize plugin, return True if successful
        return True

    def get_name(self) -> str:
        # Return display name
        return "My Plugin"

    def search(self, query: str, context: Dict) -> List[SearchResult]:
        # Perform search, return list of SearchResult objects
        return []
```

### Error Handling

**Exception Hierarchy:**
```python
class FileSearchError(Exception):
    """Base exception for all File Search errors"""
    def __init__(self, message, error_code=None, details=None):
        super().__init__(message)
        self.error_code = error_code
        self.details = details

class SearchError(FileSearchError):
    """Errors during file search operations"""
    ERROR_PERMISSION_DENIED = "SEARCH_PERMISSION_DENIED"
    ERROR_PATH_NOT_FOUND = "SEARCH_PATH_NOT_FOUND"
    # etc.

class PluginError(FileSearchError):
    """Errors related to plugin loading or execution"""
    ERROR_LOAD_FAILED = "PLUGIN_LOAD_FAILED"
    ERROR_INIT_FAILED = "PLUGIN_INIT_FAILED"
    # etc.

class ConfigError(FileSearchError):
    """Errors in configuration"""
    pass
```

**Error Recovery Pattern:**
- Continue search when encountering errors (permission denied, network drives)
- Log errors via loguru for debugging
- Show user-friendly summary: "Found 1,234 files (12 directories skipped due to permissions)"
- Never crash on individual file/directory errors

### Logging Strategy

**Configuration:**
```python
# In utils/logger.py
from loguru import logger

logger.add("logs/filesearch.log",
           rotation="5 MB",      # Rotate at 5MB
           retention="10 days",  # Keep logs for 10 days
           compression="zip",    # Compress old logs
           level="INFO",         # Default level
           format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}")
```

**Usage Pattern:**
```python
# Standard loguru format (no f-strings for performance)
logger.info("Search started in {}", directory)  # Use {} for lazy evaluation
logger.bind(search_id=123).debug("Found file: {}", filepath)  # Structured context

# No f-strings in log messages (performance)
# Use .bind() for structured logging context
```

**Log Levels:**
- `DEBUG`: Detailed diagnostic information (development only)
- `INFO`: General operational messages (search started, completed)
- `WARNING`: Potential issues (permission denied, skipped directories)
- `ERROR`: Failed operations (plugin load failed, search error)

## Data Architecture

### SearchResult Dataclass

```python
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class SearchResult:
    """Represents a single search result"""
    path: Path                    # File/folder path
    size: int                     # File size in bytes (0 for directories)
    modified: float              # Modification timestamp (from path.stat().st_mtime)
    plugin_source: Optional[str] = None  # Plugin name if from plugin, None if from core

    def get_display_name(self) -> str:
        """Return filename for display"""
        return self.path.name

    def get_display_path(self) -> str:
        """Return path with user directory abbreviated"""
        try:
            return str(self.path.relative_to(Path.home()))
        except ValueError:
            return str(self.path)

    def get_display_size(self) -> str:
        """Return human-readable file size"""
        if self.size == 0 and self.path.is_dir():
            return "Folder"

        for unit in ['B', 'KB', 'MB', 'GB']:
            if self.size < 1024.0:
                return f"{self.size:.1f} {unit}"
            self.size /= 1024.0
        return f"{self.size:.1f} TB"

    def get_display_date(self) -> str:
        """Return formatted modification date"""
        from datetime import datetime
        return datetime.fromtimestamp(self.modified).strftime('%Y-%m-%d %H:%M')
```

### Configuration Structure

QSettings keys (automatically stored in platform-appropriate location):

```
# Search settings
search/case_sensitive = false (bool)
search/include_hidden = false (bool)
search/max_results = 1000 (int)
search/default_directory = /home/user (str)
search/file_extensions_to_exclude = [".tmp", ".log", ".swp"] (str list)

# UI settings
ui/window_geometry = <QByteArray> (automatically managed by Qt)
ui/result_font_size = 12 (int)
ui/show_file_icons = true (bool)
ui/auto_expand_results = false (bool)

# Performance settings
performance/search_thread_count = 4 (int, defaults to CPU core count)
performance/enable_search_cache = false (bool)
performance/cache_ttl_minutes = 30 (int)

# Plugin settings
plugins/enabled = ["example_plugin"] (str list)
plugins/example_plugin/enabled = true (bool, per-plugin)

# Recent items
recent/searches = ["report", "meeting"] (str list, last 10)
recent/directories = ["/home/user/Documents"] (str list, last 5)
```

### Plugin Data Flow

1. **Discovery**: PluginManager scans entry_points group 'filesearch.plugins' and ~/.filesearch/plugins/*.py
2. **Loading**: Plugins imported and instantiated (subclass of SearchPlugin)
3. **Initialization**: plugin.initialize(config) called with user config
4. **Search**: plugin.search(query, context) called during search, returns List[SearchResult]
5. **Integration**: Results merged with core search results, plugin_source field identifies origin
6. **Error Handling**: Plugin failures logged but don't crash main search

## API Contracts

### Plugin Base Class

```python
from abc import ABC, abstractmethod
from typing import Dict, List, Any
from filesearch.models.search_result import SearchResult

class SearchPlugin(ABC):
    """Abstract base class for all search plugins"""

    @abstractmethod
    def initialize(self, config: Dict[str, Any]) -> bool:
        """
        Initialize plugin with configuration.

        Args:
            config: Plugin-specific configuration dictionary

        Returns:
            True if initialization successful, False otherwise
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Return display name of the plugin"""
        pass

    @abstractmethod
    def get_version(self) -> str:
        """Return version string (e.g., '1.0.0')"""
        pass

    @abstractmethod
    def search(self, query: str, context: Dict[str, Any]) -> List[SearchResult]:
        """
        Perform search using plugin-specific logic.

        Args:
            query: Search query string
            context: Search context (directory, options, etc.)

        Returns:
            List of SearchResult objects
        """
        pass

    def is_enabled(self) -> bool:
        """Check if plugin is enabled (can be overridden)"""
        return True

    def cleanup(self) -> None:
        """Cleanup resources when plugin unloaded (optional)"""
        pass
```

### Signal Signatures

```python
# In SearchEngine (QObject subclass)
class SearchEngine(QObject):
    # Emitted when a result is found
    # Parameters: filepath (Path), search_id (int)
    result_found = pyqtSignal(Path, int)

    # Emitted periodically during search
    # Parameters: files_scanned (int), current_dir (str), search_id (int)
    progress_update = pyqtSignal(int, str, int)

    # Emitted when search completes
    # Parameters: total_results (int), search_id (int)
    search_complete = pyqtSignal(int, int)

    # Emitted when error occurs
    # Parameters: error_message (str), search_id (int)
    error_occurred = pyqtSignal(str, int)

    # Emitted when search is stopped by user
    # Parameters: files_scanned (int), search_id (int)
    search_stopped = pyqtSignal(int, int)
```

### Threading Contract

```python
# UI Thread (main thread):
- Creates SearchEngine instance
- Creates QThread and moves SearchEngine to it
- Connects signals (thread-safe)
- Starts search via signal: start_search.emit(directory, query)
- Updates UI in response to signals
- Never blocks on I/O operations

# Search Thread (background):
- Executes SearchEngine.search() method
- Emits signals to communicate with UI
- Never directly updates UI widgets
- Handles file I/O and scanning
- Checks for cancellation flag periodically
- Catches exceptions and emits error_occurred signal

# Signal Safety:
- All signal emissions include search_id for correlation
- UI ignores signals from old searches (search_id mismatch)
- Signal parameters use Qt-compatible types (Path converted to str if needed)
- No complex objects in signals (use simple types or Qt types)
```

## Security Architecture

### File System Access

**Read-Only Access:**
- Application has read-only access to file system
- No file modification operations in core functionality
- File opening uses system default applications (os.startfile, xdg-open)
- Delete operations (if implemented) use system trash (send2trash library)

**Path Validation:**
- All paths validated before access: `path.exists()` and `path.is_dir()`
- Symlinks followed with cycle detection (max depth 10)
- User-provided paths sanitized (no command injection possible with pathlib)
- Network paths (UNC, NFS, SMB) supported but performance warnings shown

**Safe File Opening:**
- Executable files (.exe, .bat, .sh) show confirmation dialog
- Warning for files from untrusted locations (downloads folder)
- No automatic file execution without user action
- File type determined by extension and mime type, not content

### Plugin Security

**Sandboxing:**
- Plugins run in same process but with restricted API
- Plugin code cannot access core internals directly
- Plugin errors isolated and logged, don't crash main application
- Plugin file scanning limited to search directory scope

**Plugin Loading:**
- Only .py files loaded from plugins directory (no .pyc, no compiled extensions)
- Entry points must be explicitly registered in setup.py/pyproject.toml
- Plugin metadata (name, version, author) validated on load
- Malformed plugins skipped with error logged

### Data Protection

**Configuration Security:**
- QSettings uses platform-appropriate secure storage
- No sensitive data stored (passwords, API keys) in MVP
- Future enhancements can use keyring library for secrets
- Configuration file location not user-editable (prevents path injection)

**Logging Privacy:**
- File paths logged for debugging but can be disabled
- No personal data or content logged
- Log files stored in user-specific directory with appropriate permissions
- Log rotation prevents disk space exhaustion

## Performance Considerations

### Multi-Threaded Search Optimization

**Thread Pool Configuration:**
- Default thread count: `min(8, os.cpu_count() or 4)`
- Configurable via `performance/search_thread_count` setting
- Thread pool created once, reused for all searches
- Worker threads daemonized (don't block app exit)

**Directory Traversal:**
- Use `os.scandir()` instead of `os.listdir()` (30-50% faster)
- `os.scandir()` returns file attributes without additional stat calls
- Generator pattern yields results as found (not batching)
- Early termination when max_results reached

**Memory Efficiency:**
- Generator pattern for search results (streaming, not loading all into memory)
- Virtual scrolling in QListView (only render visible items + buffer)
- Lazy loading of file metadata (size, date) when item becomes visible
- Result list capped at max_results (default 1000, configurable to 10000)

**Performance Targets:**
- Search completion: <2 seconds for 10,000 files
- UI responsiveness: No perceptible lag during search
- Memory usage: <100MB during normal operation
- Result rendering: <100ms for 1,000 visible results
- Virtual scrolling: 60fps with 10,000+ results

### Caching Strategy

**Search Cache (MVP: disabled by default):**
- Configurable via `performance/enable_search_cache`
- Cache key: (directory, query, options hash)
- Cache TTL: `performance/cache_ttl_minutes` (default 30 minutes)
- Storage: SQLite database in user config directory
- Invalidation: Directory modification time change detection

**Icon Cache:**
- File icons cached by extension to avoid repeated lookups
- QIcon objects stored in memory-limited LRU cache
- Platform-specific icon extraction (QFileIconProvider)

**Configuration Cache:**
- QSettings values cached in memory after first access
- Cache invalidated on settings change
- Reduces file/registry access during search operations

### UI Performance

**Progress Updates:**
- Throttled to 5-10 updates per second maximum
- UI updates in batches (every 100 files or 200ms)
- Thread-safe queue for progress messages
- Atomic counters for thread-safe statistics

**Result Highlighting:**
- Highlighting computed only for visible items
- Cached when item scrolls into view
- Regex pattern pre-compiled once per search
- Case-insensitive matching using `re.IGNORECASE`

**Sorting Optimization:**

**SortEngine Architecture:**
- Central `SortEngine` class with static methods for each sort type (name, size, date, type, relevance)
- Natural sorting for filenames using `natsort` library (file1, file2, file10 - not file1, file10, file2)
- Relevance scoring algorithm: exact match (100) > starts with (80-100) > contains (40-60) > ends with (20-50)
- Five sort criteria supported:
  - Name (A-Z/Z-A) with folder grouping
  - Size (smallest/largest) with folders at top/bottom
  - Date (newest/oldest first)
  - Type (folders first, then files by extension)
  - Relevance (based on query position in filename)

**Performance Targets (AC1-AC5):**
- Name sort: <100ms for 1,000 items
- Size sort: <200ms for 10,000 items
- Date sort: Selection preservation maintained (scroll position tracked in AC3)
- Type sort: Stable sort maintains relative order
- Relevance sort: Calculated once per item, O(n log n) overall

**Implementation Details:**
- No background threading for MVP (MVP target <1K results)
- Simple `list.sort()` or `sorted()` operations
- Stable sort algorithms (maintain relative order of equal elements)
- Folder detection via `path.is_dir()` (0-size marking not used for sorting)
- Type grouping: folders (0, name) first, then files (1, ext, name)
- Relevance sorting requires active search query (falls back to name if no query)

**UI Integration:**
- SortControls widget provides dropdown with all sort options
- Visual indicator (arrow) shows current sort direction
- Keyboard shortcuts: Ctrl+1..5 for criteria, Ctrl+R to reverse
- Sort state persists across searches (saved in config)
- Selection preservation attempts to re-select same item after sort

**Configuration Integration:**
- Sort criteria saved to `sorting.criteria` in QSettings
- Default: name_asc (Name A-Z)
- Automatically applied on app launch (restored from config)

## Deployment Architecture

### Development Environment

**Prerequisites:**
- Python 3.9 or higher
- pip (Python package manager)
- Git (for version control)
- Virtual environment support (venv)

**Platform-Specific Requirements:**
- **Windows**: Windows 10+, Visual C++ Redistributable (usually pre-installed)
- **macOS**: macOS 10.14+, Xcode Command Line Tools
- **Linux**: Ubuntu 18.04+ or CentOS 7+, Qt dependencies (usually pre-installed)

### Setup Commands

```bash
# Clone repository
git clone <repository-url>
cd filesearch

# Create virtual environment
python -m venv venv

# Activate virtual environment
# Linux/Mac:
source venv/bin/activate
# Windows:
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/ -v

# Run application
python -m src.filesearch.main

# Build executable (optional)
python scripts/build_executable.py
```

### Distribution Options

**PyInstaller (Recommended for MVP):**
- Single executable for each platform
- Bundles Python interpreter and all dependencies
- Command: `pyinstaller --onefile --windowed --name FileSearch src/filesearch/main.py`
- Output: FileSearch.exe (Windows), FileSearch.app (macOS), FileSearch (Linux)
- Size: ~50-100MB per platform

**Platform-Specific Packages:**
- **Windows**: Inno Setup installer or MSI
- **macOS**: DMG disk image or Homebrew formula
- **Linux**: DEB package (Ubuntu/Debian), RPM package (Fedora/CentOS), or PyPI package

**PyPI Package (Advanced Users):**
- `pip install filesearch`
- Command-line entry point: `filesearch`
- Requires user to install Python and PyQt6 dependencies
- Smaller distribution, more complex user setup

### Build Process

```bash
# Install PyInstaller
pip install pyinstaller

# Build for current platform
pyinstaller scripts/filesearch.spec

# Output in dist/ directory
# - Windows: dist/FileSearch.exe
# - macOS: dist/FileSearch.app
# - Linux: dist/FileSearch
```

**Build Script Features:**
- Platform detection and appropriate options
- Icon inclusion (.ico for Windows, .icns for macOS)
- Hidden imports for PyQt6 plugins
- UPX compression (optional, reduces size)
- Code signing (macOS and Windows)

## Architecture Decision Records (ADRs)

### ADR-001: PyQt6 as GUI Framework

**Decision:** Use PyQt6 for cross-platform GUI

**Rationale:**
- Native look and feel on Windows, macOS, and Linux
- Excellent threading support (QThread, signals/slots)
- Rich widget set perfect for file search UI
- QSettings for cross-platform configuration
- QFileDialog for native directory selection
- Professional appearance out of the box

**Tradeoffs:**
- External dependency (but very stable and well-maintained)
- GPL license requires commercial license for closed-source distribution
- Larger distribution size compared to Tkinter

**Status:** Accepted

### ADR-002: Multi-Threaded Search

**Decision:** Implement multi-threaded search using concurrent.futures.ThreadPoolExecutor

**Rationale:**
- Meets <2 second performance requirement for 10,000 files
- Keeps UI responsive during search operations
- Scales to 100,000 files (NFR requirement)
- Utilizes multiple CPU cores for I/O-bound operations
- Python's GIL less problematic for file I/O

**Tradeoffs:**
- More complex than single-threaded approach
- Need careful thread synchronization
- Higher memory usage (but within 100MB limit)
- Testing requires thread-aware test cases

**Status:** Accepted

### ADR-003: Plugin Architecture

**Decision:** Hybrid plugin discovery (entry points + directory scanning)

**Rationale:**
- Entry points for distributed plugins (PyPI packages)
- Directory scanning for user-developed plugins
- Maximum flexibility for future extensibility
- Plugin architecture enables folder visualization feature (vision)
- Error isolation prevents plugin crashes from affecting core

**Tradeoffs:**
- More complex plugin loading logic
- Security considerations for user plugins
- Need clear plugin API documentation

**Status:** Accepted

### ADR-004: QSettings for Configuration

**Decision:** Use QSettings for cross-platform configuration storage

**Rationale:**
- Automatic platform-appropriate storage (Registry on Windows, plist on macOS, INI on Linux)
- Type-safe value storage
- No file format or location decisions needed
- Atomic saves prevent corruption
- Used by thousands of Qt applications

**Tradeoffs:**
- Not human-editable (stored in platform-specific format)
- Harder to sync across machines
- But much more robust than manual file management

### ADR-009: JSON Configuration Files

**Decision:** Use JSON files with platformdirs for configuration storage

**Rationale:**
- Human-readable and manually editable format meets explicit user requirement (AC4)
- Cross-platform directory detection using platformdirs library
- Simple JSON parsing with built-in Python support
- Easy to version and migrate configurations
- Supports comments in JSON (implementation allows)

**Tradeoffs:**
- Less robust than QSettings (no atomic saves, potential corruption)
- Requires manual file management and validation
- But provides the required human-editable configuration

**Status:** Accepted (supersedes ADR-004 for MVP implementation)

**Status:** Accepted

### ADR-005: loguru for Logging

**Decision:** Use loguru library for structured logging

**Rationale:**
- Modern, user-friendly API compared to standard logging
- Automatic rotation, retention, compression built-in
- Structured logging with .bind() for context
- Colored console output during development
- Excellent performance and thread-safety
- Single dependency, very stable (10K+ stars)

**Tradeoffs:**
- External dependency (but very lightweight)
- Not standard library (but de facto standard for many projects)

**Status:** Accepted

### ADR-006: pathlib.Path for File Operations

**Decision:** Use pathlib.Path throughout codebase

**Rationale:**
- Modern Python standard (since 3.4, using 3.9+)
- Object-oriented and readable: `path / "subdir" / "file.txt"`
- Cross-platform path separators handled automatically
- Type-safe with excellent type hint support
- Rich API for all file operations needed
- Recommended by Python community

**Tradeoffs:**
- Slightly different API than traditional os.path
- Newer developers might need to learn it
- But it's the modern Python way

**Status:** Accepted

### ADR-007: pytest with pytest-qt for Testing

**Decision:** Use pytest with pytest-qt plugin for testing

**Rationale:**
- pytest is de facto standard for Python testing
- pytest-qt handles tricky Qt testing issues automatically:
  - Event loop management
  - Widget lifetime and cleanup
  - Signal testing utilities
  - Keyboard/mouse event simulation
- Great for testing multi-threaded search (can wait for signals)
- Fixtures make test setup clean and reusable

**Tradeoffs:**
- Additional dependency (pytest-qt)
- Learning curve for pytest fixtures

**Status:** Accepted

### ADR-008: Continue on Error for Search

**Decision:** Continue search when encountering errors, log and show summary

**Rationale:**
- Users want results even if some directories are inaccessible
- System directories often have permission restrictions
- Network drives may be temporarily unavailable
- loguru captures errors for debugging
- Better user experience than fail-fast approach

**Tradeoffs:**
- Users may not notice some files were skipped
- Need clear UI indication of skipped items
- But more resilient and useful overall

**Status:** Accepted

---

_Generated by BMAD Decision Architecture Workflow v1.0_
_Date: 2025-11-13_
_For: Matt_
