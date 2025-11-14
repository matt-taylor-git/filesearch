# Story 1.2: Implement Modular Code Structure

Status: ready-for-dev

## Story

As a developer,
I want a modular code architecture with clear separation of concerns,
So that new features can be added without modifying core search logic.

## Acceptance Criteria

**Given** the project infrastructure from Story 1.1  
**When** I implement the modular structure  
**Then** the following core modules should be created:

### 1. Core Search Engine Module
- **File**: `src/filesearch/core/search_engine.py`
- **Class**: `FileSearchEngine` with `search(directory, query)` method
- **Returns**: Generator yielding file paths matching query
- **Features**:
  - Supports partial matching using `fnmatch` or custom algorithm
  - Implements early termination when max results reached
  - Multi-threaded directory traversal using `concurrent.futures.ThreadPoolExecutor`
  - Uses `os.scandir()` for efficient file system walking
  - Generator pattern for memory-efficient result streaming
  - Real-time result streaming capability
  - Cancelable search operation

### 2. File Utilities Module
- **File**: `src/filesearch/core/file_utils.py`
- **Functions**:
  - `get_file_info(path)` - Returns dict with size, modified time, type
  - `safe_open(path)` - Opens file with system default application
  - `open_containing_folder(path)` - Opens directory in file manager
- **Features**:
  - Cross-platform implementation using `os.startfile`, `subprocess`, or `QDesktopServices`
  - Proper error handling for permission denied and file not found
  - Support for Unicode filenames and paths

### 3. Configuration Manager Module
- **File**: `src/filesearch/core/config_manager.py`
- **Class**: `ConfigManager` for loading/saving user preferences
- **Features**:
  - Supports JSON configuration file format
  - Default config location: `~/.filesearch/config.json` (cross-platform)
  - Methods: `get(key, default)`, `set(key, value)`, `save()`, `load()`
  - Uses `platformdirs` for cross-platform config directory detection
  - Auto-creates config with default values on first launch
  - Validates configuration on load

### 4. Plugin Base Module
- **File**: `src/filesearch/plugins/plugin_base.py`
- **Class**: Abstract base class `SearchPlugin`
- **Methods**: `initialize()`, `search()`, `get_name()`
- **Features**:
  - Plugin metadata support (name, version, author, description)
  - Plugin discovery mechanism using entry points or directory scanning
  - Abstract base class using `abc.ABC` and `@abstractmethod`

### 5. Main GUI Window Module
- **File**: `src/filesearch/ui/main_window.py`
- **Class**: `MainWindow` with search input, directory selector, results display
- **Features**:
  - Separated from business logic (uses search_engine module)
  - Event-driven architecture with signals/slots (Qt)
  - Depends on Core modules but Core has no UI dependencies

**And** each module should have:
- Comprehensive unit tests in `/tests/unit/` with >80% coverage
- Type hints for all public methods (Python 3.9+ compatibility)
- Error handling with specific exception types from `core/exceptions.py`
- Logging integration using loguru
- Google or NumPy style docstrings

**And** the module dependencies should flow in one direction:
- UI depends on Core modules
- Core modules have no UI dependencies
- Plugins depend on Plugin Base
- Config Manager is standalone

## Tasks / Subtasks

### Core Search Engine Implementation
- [x] Create `src/filesearch/core/search_engine.py`
  - [x] Implement `FileSearchEngine` class with `search()` method
  - [x] Add multi-threaded directory traversal using `ThreadPoolExecutor`
  - [x] Implement partial matching using `fnmatch` or custom algorithm
  - [x] Add early termination when max results reached
  - [x] Implement generator pattern for result streaming
  - [x] Add search cancellation support
  - [x] Integrate logging with loguru
  - [x] Add comprehensive type hints
  - [x] Write Google-style docstrings

### File Utilities Implementation
- [x] Create `src/filesearch/core/file_utils.py`
  - [x] Implement `get_file_info(path)` function
  - [x] Implement `safe_open(path)` for cross-platform file opening
  - [x] Implement `open_containing_folder(path)` for folder navigation
  - [x] Add proper error handling for edge cases
  - [x] Support Unicode filenames and paths
  - [x] Integrate logging with loguru
  - [x] Add comprehensive type hints
  - [x] Write Google-style docstrings

### Configuration Manager Implementation
- [x] Create `src/filesearch/core/config_manager.py`
  - [x] Implement `ConfigManager` class
  - [x] Add `get(key, default)`, `set(key, value)`, `save()`, `load()` methods
  - [x] Use `platformdirs` for cross-platform config directory detection
  - [x] Implement JSON configuration file format
  - [x] Add auto-creation of config with default values
  - [x] Implement configuration validation on load
  - [x] Integrate logging with loguru
  - [x] Add comprehensive type hints
  - [x] Write Google-style docstrings

### Plugin Base Implementation
- [x] Create `src/filesearch/plugins/plugin_base.py`
  - [x] Implement abstract base class `SearchPlugin`
  - [x] Add abstract methods: `initialize()`, `search()`, `get_name()`
  - [x] Add plugin metadata support (name, version, author, description)
  - [x] Implement plugin discovery mechanism
  - [x] Use `abc.ABC` and `@abstractmethod` decorators
  - [x] Integrate logging with loguru
  - [x] Add comprehensive type hints
  - [x] Write Google-style docstrings

### Main GUI Window Implementation
- [x] Create `src/filesearch/ui/main_window.py`
  - [x] Implement `MainWindow` class
  - [x] Add search input field
  - [x] Add directory selector
  - [x] Add results display area
  - [x] Implement event-driven architecture with signals/slots
  - [x] Ensure separation from business logic
  - [x] Integrate logging with loguru
  - [x] Add comprehensive type hints
  - [x] Write Google-style docstrings

### Unit Testing
- [x] Create `tests/unit/test_search_engine.py`
  - [x] Write tests for `FileSearchEngine` class
  - [x] Test multi-threaded search functionality
  - [x] Test partial matching algorithms
  - [x] Test early termination
  - [x] Test search cancellation
  - [x] Achieve >80% coverage

- [x] Create `tests/unit/test_file_utils.py`
  - [x] Write tests for `get_file_info()` function
  - [x] Write tests for `safe_open()` function
  - [x] Write tests for `open_containing_folder()` function
  - [x] Test cross-platform compatibility
  - [x] Test error handling
  - [x] Achieve >80% coverage

- [x] Create `tests/unit/test_config_manager.py`
  - [x] Write tests for `ConfigManager` class
  - [x] Test configuration loading and saving
  - [x] Test default value handling
  - [x] Test validation
  - [x] Test cross-platform directory detection
  - [x] Achieve >80% coverage

- [x] Create `tests/unit/test_plugin_base.py`
  - [x] Write tests for `SearchPlugin` abstract class
  - [x] Test plugin discovery mechanism
  - [x] Test plugin initialization
  - [x] Test metadata handling
  - [x] Achieve >80% coverage

- [x] Create `tests/unit/test_main_window.py`
  - [x] Write tests for `MainWindow` class
  - [x] Test UI component initialization
  - [x] Test event handling
  - [x] Test signal/slot connections
  - [x] Achieve >80% coverage

### Integration and Code Quality
- [x] All core modules implemented with comprehensive unit tests
- [x] Type hints added for all public methods (Python 3.9+ compatibility)
- [x] Google-style docstrings written for all modules and public functions
- [x] Error handling implemented using custom exception hierarchy from `core/exceptions.py`
- [x] Logging integrated using loguru with structured logging
- [x] Module dependencies flow in one direction: UI → Core → Plugins
- [x] Cross-platform support implemented for file operations and config directories

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Modular Architecture:**
- Clear separation of concerns with 5 distinct modules
- One-way dependency flow (UI → Core → Plugins)
- Each module has single, well-defined responsibility

**Technology Stack Alignment:**
- **PyQt6**: For UI components (main_window.py)
- **loguru**: For logging integration in all modules
- **pytest**: For comprehensive unit testing
- **platformdirs**: For cross-platform config directory detection
- **concurrent.futures**: For multi-threaded search implementation

**Code Quality Standards (from Story 1.1):**
- Type hints for all public methods (Python 3.9+ compatibility)
- Google-style docstrings on all modules and public functions
- Error handling using custom exception hierarchy from `core/exceptions.py`
- Logging integration using loguru with structured logging

**Design Patterns:**
- **Abstract Base Class**: For plugin architecture (SearchPlugin)
- **Generator Pattern**: For memory-efficient search results streaming
- **Dependency Injection**: UI receives search_engine instance
- **Singleton Pattern**: ConfigManager likely to be singleton

### Source Tree Components to Touch

**New Files to Create:**
- `src/filesearch/core/search_engine.py` - Core search functionality
- `src/filesearch/core/file_utils.py` - File system operations
- `src/filesearch/core/config_manager.py` - Configuration management
- `src/filesearch/plugins/plugin_base.py` - Plugin base class
- `src/filesearch/ui/main_window.py` - Main GUI window
- `tests/unit/test_search_engine.py` - Search engine tests
- `tests/unit/test_file_utils.py` - File utilities tests
- `tests/unit/test_config_manager.py` - Config manager tests
- `tests/unit/test_plugin_base.py` - Plugin base tests
- `tests/unit/test_main_window.py` - Main window tests

**Existing Files to Reference:**
- `src/filesearch/core/exceptions.py` - Error handling framework
- `src/filesearch/__init__.py` - Package structure
- `pyproject.toml` - Project metadata and dependencies

### Testing Standards Summary

**Framework**: pytest with pytest-qt for UI components
- Unit tests for each module in `/tests/unit/`
- Target: >80% code coverage for each module
- Test file naming: `test_*.py`
- Use fixtures for common test setup

**Test Categories:**
- **Happy path tests**: Normal operation scenarios
- **Edge case tests**: Boundary conditions, empty inputs, maximum values
- **Error handling tests**: Exceptions, permission errors, file not found
- **Cross-platform tests**: Platform-specific behavior where applicable

**Coverage Goals:**
- All public methods tested
- Error paths tested
- Integration between modules tested
- UI event handling tested (for main_window.py)

### References

- **Architecture**: [Source: docs/architecture.md#Epic-to-Architecture-Mapping]
- **PRD**: [Source: docs/PRD.md#Functional-Requirements]
- **Epics**: [Source: docs/epics.md#Story-1.2:-Implement-Modular-Code-Structure]
- **Previous Story**: [Source: docs/sprint-artifacts/1-1-project-setup-and-core-infrastructure.md]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/stories/1-2-implement-modular-code-structure.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

**Files Created:**
- `src/filesearch/core/search_engine.py` - Multi-threaded file search engine with generator-based streaming
- `src/filesearch/core/file_utils.py` - Cross-platform file operations and utilities
- `src/filesearch/core/config_manager.py` - JSON configuration management with platformdirs
- `src/filesearch/plugins/plugin_base.py` - Abstract base class for search plugins
- `src/filesearch/ui/main_window.py` - Main GUI window with event-driven architecture
- `tests/unit/test_search_engine.py` - Comprehensive tests for search engine
- `tests/unit/test_file_utils.py` - Comprehensive tests for file utilities
- `tests/unit/test_config_manager.py` - Comprehensive tests for config manager
- `tests/unit/test_plugin_base.py` - Comprehensive tests for plugin base
- `tests/unit/test_main_window.py` - Comprehensive tests for main window

**Files Referenced:**
- `src/filesearch/core/exceptions.py` - Custom exception hierarchy
- `src/filesearch/__init__.py` - Package initialization
- `pyproject.toml` - Project metadata
- `requirements.txt` - Runtime dependencies
- `requirements-dev.txt` - Development dependencies

## Change Log

- **2025-11-14**: Story drafted by SM agent
- **Status**: drafted (was: backlog)
- **2025-11-14**: Core modules implemented by Dev agent
  - Created search_engine.py with FileSearchEngine class
  - Created file_utils.py with cross-platform file operations
  - Created config_manager.py with JSON configuration management
  - Created plugin_base.py with SearchPlugin abstract class
  - Created main_window.py with MainWindow UI class
  - Created comprehensive unit tests for all modules
  - Status: review (was: in-progress)
- **2025-11-14**: Story implementation completed
  - All 5 core modules implemented and tested
  - All acceptance criteria satisfied
  - Module dependency flow verified (UI → Core → Plugins)
  - Status: done (was: review)
