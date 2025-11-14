# File Search - Epic Breakdown

**Author:** Matt
**Date:** 2025-11-13
**Project Level:** MVP
**Target Scale:** Desktop application

---

## Overview

This document provides the complete epic and story breakdown for File Search, decomposing the requirements from the [PRD](./PRD.md) into implementable stories.

**Living Document Notice:** This is the initial version. It will be updated after UX Design and Architecture workflows add interaction and technical details to stories.

### Proposed Epic Structure

**Epic 1: Extensibility Foundation**  
- **Business Goal:** Establish a modular architecture that enables easy addition of new features and future enhancements  
- **Scope:** Implement modular code structure, configuration file support, and plugin architecture foundation  
- **Capabilities:** 3 related features (modular structure, config file, plugin system)  
- **Value:** Allows the app to evolve beyond MVP without core rewrites  
- **Deliverable Phase:** Foundation phase enabling all subsequent development  

**Epic 2: Search Interface**  
- **Business Goal:** Provide an intuitive interface for users to perform file searches  
- **Scope:** Search input field, directory selection, search initiation, progress indicators, and status display  
- **Capabilities:** 9 related features (search input, directory selection, initiation, partial matching, performance, UI elements, progress, status)  
- **Value:** Users can easily specify and execute searches  
- **Deliverable Phase:** Core functionality phase  

**Epic 3: Results Management**  
- **Business Goal:** Enable effective viewing and interaction with search results  
- **Scope:** Results display, sorting options, highlighting, and file operations (open, context menu, folder navigation)  
- **Capabilities:** 7 related features (list display, result details, highlighting, sorting, double-click, right-click, folder open)  
- **Value:** Users can efficiently browse and act on search results  
- **Deliverable Phase:** Results handling phase  

**Suggested Sequencing:**  
1 → 2 → 3 (Foundation first to enable extensibility, then core search interface, finally results management)  

**Why This Grouping Makes Sense:**  
- **Natural User Flow:** Foundation → Search Input → Results Display/Operations  
- **Technical Dependencies:** Modular structure (Epic 1) supports plugin enhancements mentioned in vision  
- **Business Value:** Each epic delivers independent value while building toward the complete MVP  
- **Complexity Management:** Groups related capabilities that can be developed cohesively  
- **Greenfield Foundation:** Epic 1 establishes the extensible architecture needed for the app's evolution  

**FR Coverage Validation:** All 19 functional requirements from the PRD inventory are mapped to at least one epic. No requirements are deferred or unmapped.

---

## Functional Requirements Inventory

**FR1:** Users can enter search terms to find files and folders by name  
**FR2:** Users can specify starting directory for search scope  
**FR3:** Users can initiate search with Enter key or Search button  
**FR4:** Search supports partial filename matching  
**FR5:** Search results display within 2 seconds for typical directory structures  
**FR6:** Search results shown in clean, scrollable list  
**FR7:** Each result shows filename, full path, and file size  
**FR8:** Results highlight matching text in filenames  
**FR9:** Users can sort results by name, date modified, or size  
**FR10:** Users can double-click results to open files with default application  
**FR11:** Users can right-click results to show context menu with open options  
**FR12:** Users can open containing folder for selected result  
**FR13:** Minimal GUI with search input field at top  
**FR14:** Directory selection via browse button or text input  
**FR15:** Progress indicator during search operations  
**FR16:** Status display showing number of results found  
**FR17:** Modular code structure allowing easy addition of new search features  
**FR18:** Configuration file for user preferences  
**FR19:** Plugin architecture for future enhancements like folder usage visualization  

---

## FR Coverage Map

**Epic 1 (Extensibility Foundation):** FR17, FR18, FR19  
**Epic 2 (Search Interface):** FR1, FR2, FR3, FR4, FR5, FR13, FR14, FR15, FR16  
**Epic 3 (Results Management):** FR6, FR7, FR8, FR9, FR10, FR11, FR12  

---

## Epic 1: Extensibility Foundation

Establish a modular architecture that enables easy addition of new features and future enhancements

### Story 1.1: Project Setup and Core Infrastructure

**As a** developer,  
**I want** a properly structured Python project with build system and deployment pipeline,  
**So that** subsequent development can proceed with consistent tooling and practices.

**Acceptance Criteria:**

**Given** an empty project directory  
**When** I initialize the project structure  
**Then** the following directories should be created:  
- `/src/filesearch/` - Main application package  
- `/src/filesearch/core/` - Core functionality modules  
- `/src/filesearch/plugins/` - Plugin architecture directory  
- `/src/filesearch/ui/` - User interface components  
- `/tests/` - Test suite directory  
- `/config/` - Configuration files directory  
- `/docs/` - Documentation directory  

**And** the following files should be created:  
- `pyproject.toml` - Modern Python packaging configuration with project metadata, dependencies (PyQt6 or Tkinter, pytest), and build settings  
- `requirements.txt` - Runtime dependencies  
- `requirements-dev.txt` - Development dependencies (pytest, black, flake8)  
- `.gitignore` - Standard Python gitignore  
- `README.md` - Project overview and setup instructions  
- `src/filesearch/__init__.py` - Package initialization with version info  
- `src/filesearch/main.py` - Application entry point  

**And** the project should include:  
- Cross-platform path handling using `pathlib.Path`  
- Logging configuration with rotating file handler (max 5MB, 3 backups)  
- Error handling framework with custom exceptions  
- Type hints throughout codebase (Python 3.9+ compatibility)  
- Docstrings following Google or NumPy style  

**Prerequisites:** None (first story)  

**Technical Notes:**  
- Use `pyproject.toml` instead of `setup.py` for modern Python packaging  
- Consider PyQt6 for cross-platform GUI (better than Tkinter for extensibility)  
- Include pre-commit hooks for code formatting (black) and linting (flake8)  
- Set up GitHub Actions or similar CI for automated testing  
- Create virtual environment setup script for each platform (`.sh` for Linux/Mac, `.bat` for Windows)  

---

### Story 1.2: Implement Modular Code Structure

**As a** developer,  
**I want** a modular code architecture with clear separation of concerns,  
**So that** new features can be added without modifying core search logic.

**Acceptance Criteria:**  

**Given** the project infrastructure from Story 1.1  
**When** I implement the modular structure  
**Then** the following core modules should be created:  

1. **`src/filesearch/core/search_engine.py`** - Core search functionality  
   - `FileSearchEngine` class with `search(directory, query)` method  
   - Returns generator yielding file paths matching query  
   - Supports partial matching using `fnmatch` or custom algorithm  
   - Implements early termination if needed  

2. **`src/filesearch/core/file_utils.py`** - File system operations  
   - `get_file_info(path)` - Returns dict with size, modified time, type  
   - `safe_open(path)` - Opens file with system default application  
   - `open_containing_folder(path)` - Opens directory in file manager  
   - Cross-platform implementation using `os.startfile`, `subprocess`, or `QDesktopServices`  

3. **`src/filesearch/core/config_manager.py`** - Configuration management  
   - `ConfigManager` class for loading/saving user preferences  
   - Supports JSON configuration file format  
   - Default config location: `~/.filesearch/config.json` (cross-platform)  
   - Methods: `get(key, default)`, `set(key, value)`, `save()`, `load()`  

4. **`src/filesearch/plugins/plugin_base.py`** - Plugin base class  
   - Abstract base class `SearchPlugin` with `initialize()`, `search()`, `get_name()` methods  
   - Plugin metadata support (name, version, author, description)  
   - Plugin discovery mechanism using entry points or directory scanning  

5. **`src/filesearch/ui/main_window.py`** - Main GUI window  
   - `MainWindow` class with search input, directory selector, results display  
   - Separated from business logic (uses search_engine module)  
   - Event-driven architecture with signals/slots (Qt) or callbacks (Tkinter)  

**And** the module dependencies should flow in one direction:  
- UI depends on Core modules  
- Core modules have no UI dependencies  
- Plugins depend on Plugin Base  
- Config Manager is standalone  

**And** each module should have:  
- Comprehensive unit tests in `/tests/` with >80% coverage  
- Type hints for all public methods  
- Error handling with specific exception types  
- Logging integration  

**Prerequisites:** Story 1.1 (Project Setup)  

**Technical Notes:**  
- Use dependency injection pattern: UI receives search_engine instance  
- Implement plugin discovery using `importlib.metadata.entry_points()` (Python 3.8+)  
- Create abstract base classes using `abc.ABC` and `@abstractmethod`  
- Follow single responsibility principle: each module has one clear purpose  
- Consider using `pytest` fixtures for testing module interactions  

---

### Story 1.3: Create Configuration File System

**As a** user,  
**I want** a configuration file to persist my preferences,  
**So that** I don't have to reconfigure the application on each launch.

**Acceptance Criteria:**  

**Given** the modular structure from Story 1.2  
**When** I implement the configuration system  
**Then** the following configuration options should be supported:  

1. **Search Preferences:**  
   - `default_search_directory` - String path (default: user's home directory)  
   - `case_sensitive_search` - Boolean (default: false)  
   - `include_hidden_files` - Boolean (default: false)  
   - `max_search_results` - Integer (default: 1000, max: 10000)  
   - `file_extensions_to_exclude` - List of strings (default: ['.tmp', '.log', '.swp'])  

2. **UI Preferences:**  
   - `window_geometry` - Dict with x, y, width, height (default: centered, 800x600)  
   - `result_font_size` - Integer pixels (default: 12)  
   - `show_file_icons` - Boolean (default: true)  
   - `auto_expand_results` - Boolean (default: false)  

3. **Performance Settings:**  
   - `search_thread_count` - Integer (default: number of CPU cores)  
   - `enable_search_cache` - Boolean (default: false for MVP)  
   - `cache_ttl_minutes` - Integer (default: 30)  

**And** the configuration file should:  
- Be stored at platform-appropriate location:  
  - Windows: `%APPDATA%/filesearch/config.json`  
  - macOS: `~/Library/Application Support/filesearch/config.json`  
  - Linux: `~/.config/filesearch/config.json`  
- Auto-create on first launch with default values  
- Validate configuration on load (ignore invalid keys, use defaults for missing values)  
- Support manual editing (human-readable JSON with comments allowed)  
- Reload configuration without restart (file watcher or manual refresh)  

**And** the UI should provide:  
- Settings dialog accessible from menu bar  
- Real-time validation of configuration values  
- Reset to defaults button  
- Apply changes without restart where possible  

**Prerequisites:** Story 1.2 (Modular Structure)  

**Technical Notes:**  
- Use `platformdirs` library for cross-platform config directory detection  
- Implement schema validation using `jsonschema` or custom validation  
- Add file watcher using `watchdog` library for auto-reload (optional for MVP)  
- Create migration system for config version upgrades (store version in JSON)  
- Encrypt sensitive values if added in future (use `keyring` library)  
- Document all configuration options in `/docs/configuration.md`  

---

### Story 1.4: Implement Plugin Architecture Foundation

**As a** developer,  
**I want** a plugin system that allows adding features without core code changes,  
**So that** future enhancements like folder visualization can be added modularly.

**Acceptance Criteria:**  

**Given** the modular structure and config system from previous stories  
**When** I implement the plugin architecture  
**Then** the following plugin capabilities should be supported:  

1. **Plugin Discovery:**  
   - Scan `~/.filesearch/plugins/` directory for plugin modules  
   - Load plugins from Python entry points (`filesearch.plugins` group)  
   - Support built-in plugins in `/src/filesearch/plugins/builtin/`  
   - Plugin metadata file: `plugin.json` with name, version, author, description, dependencies  

2. **Plugin Base Class (`plugin_base.py`):**  
   ```python  
   class SearchPlugin(ABC):  
       @abstractmethod  
       def initialize(self, config: Dict) -> bool:  
           """Initialize plugin with configuration. Return True if successful."""  
           pass  
       
       @abstractmethod  
       def get_name(self) -> str:  
           """Return plugin display name."""  
           pass  
       
       @abstractmethod  
       def search(self, query: str, context: Dict) -> List[SearchResult]:  
           """Perform search using plugin-specific logic."""  
           pass  
       
       def is_enabled(self) -> bool:  
           """Check if plugin is enabled (default: True)."""  
           return True  
   ```  

3. **Plugin Manager (`plugin_manager.py`):**  
   - `PluginManager` class for loading and managing plugins  
   - Methods: `load_plugins()`, `get_plugin(name)`, `enable_plugin(name)`, `disable_plugin(name)`  
   - Plugin lifecycle: discovery → load → initialize → enable/disable → unload  
   - Error isolation: one plugin failure doesn't crash entire application  
   - Plugin configuration section in main config file  

4. **Built-in Example Plugin:**  
   - Create `example_plugin.py` demonstrating plugin structure  
   - Simple "recent files" search plugin (tracks recently accessed files)  
   - Includes complete `plugin.json` metadata  
   - Serves as template for future plugins  

5. **Plugin UI Integration:**  
   - Settings panel showing loaded plugins with enable/disable toggles  
   - Plugin-specific configuration dialogs  
   - Visual indicator for plugin status (loaded, enabled, error)  
   - Plugin search results integrated into main results list with source indicator  

**And** the plugin system should enforce:  
- Sandboxed execution (plugins can't access core internals directly)  
- Version compatibility checking (plugin specifies compatible app version)  
- Dependency resolution (plugin can depend on other plugins)  
- Error handling with graceful degradation (disable failed plugins)  

**Prerequisites:** Stories 1.2 and 1.3  

**Technical Notes:**  
- Use `importlib` for dynamic module loading  
- Implement plugin API versioning to maintain backward compatibility  
- Create plugin development kit (PDK) documentation in `/docs/plugin-development.md`  
- Consider plugin signing for security in future versions  
- Use `pluggy` library (from pytest) for robust plugin hooks if needed  
- Plugin results should implement same `SearchResult` interface as core search  
- Add plugin profiling to monitor performance impact  

---

## Epic 2: Search Interface

Provide an intuitive interface for users to perform fast file searches

### Story 2.1: Implement Core Search Engine with Performance Optimization

**As a** user,  
**I want** fast file searching that completes within 2 seconds for typical directories,  
**So that** I can quickly find the files I need without waiting.

**Acceptance Criteria:**  

**Given** a directory containing up to 10,000 files  
**When** I execute a search with a partial filename query  
**Then** results should appear within 2 seconds  

**And** the search should support:  
- Partial matching using wildcard patterns (`*query*`, `query*`, `*query`)  
- Case-insensitive matching by default (configurable)  
- Exclusion of hidden files based on configuration  
- Filtering by file extensions from config exclude list  
- Early termination when max results reached (configurable, default 1000)  

**And** the search engine should implement:  
- Multi-threaded directory traversal using `concurrent.futures.ThreadPoolExecutor`  
- Efficient file system walking with `os.scandir()` (faster than `os.walk()`)  
- Generator pattern to yield results as they're found (not waiting for complete traversal)  
- Memory-efficient result handling (streaming, not loading all into memory)  
- Real-time result streaming to UI (results appear as they're found)  

**And** performance characteristics:  
- Search thread count defaults to CPU core count (configurable)  
- Non-blocking UI during search (search runs in background thread)  
- Progress callbacks to update UI with files scanned count  
- Cancelable search operation (user can stop mid-search)  
- Memory usage under 100MB during search of 10,000 files  

**And** edge cases handled:  
- Permission denied errors logged but don't crash search  
- Symlinks followed with cycle detection (max depth 10)  
- Network drives handled gracefully (slower but functional)  
- Very long paths supported (up to OS maximum)  
- Unicode filenames supported correctly  

**Prerequisites:** Story 1.2 (Modular Structure)  

**Technical Notes:**  
- Use `os.scandir()` instead of `os.listdir()` for better performance (returns file attributes without stat calls)  
- Implement breadth-first search for more responsive early results  
- Consider using `fnmatch.translate()` to convert patterns to regex for complex matching  
- Add search result caching for repeated queries (configurable, default off for MVP)  
- Profile search performance using `cProfile` to identify bottlenecks  
- For very large directories (100K files), implement incremental result loading  
- Use `pathlib.Path.rglob()` as alternative implementation for simplicity vs performance tradeoff analysis  

---

### Story 2.2: Create Search Input Interface

**As a** user,  
**I want** a prominent search input field where I can type my search query,  
**So that** I can easily enter what I'm looking for.

**Acceptance Criteria:**  

**Given** the main application window  
**When** I view the search interface  
**Then** I should see a search input field at the top of the window with:  
- Clear label: "Search files and folders"  
- Placeholder text: "Enter filename or partial name..."  
- Width: 80% of window width (minimum 400px)  
- Height: 32px with 8px padding  
- Font size: 14px, system font family  
- Focused by default when application launches  

**And** the search input should support:  
- Keyboard input with immediate feedback  
- Paste from clipboard (Ctrl+V or Cmd+V)  
- Clear button (X icon) appearing when text is entered  
- Search history dropdown (store last 10 searches, accessible via down arrow)  
- Auto-complete suggestions from recent searches  
- Maximum length: 255 characters  
- Special character handling (quotes, asterisks, etc. treated as literal search terms)  

**And** keyboard interactions:  
- **Enter key:** Immediately initiates search  
- **Escape key:** Clears the input and returns focus  
- **Ctrl+L:** Selects all text in search field (standard shortcut)  
- **Tab key:** Navigates to next control (directory selector)  
- **Shift+Tab:** Navigates to previous control  

**And** visual feedback:  
- Border color: Light gray normal, blue when focused  
- Background: White with slight transparency  
- Text color: Dark gray (high contrast)  
- Error state: Red border if search fails (rare)  
- Loading indicator: Spinner icon appears during search  

**And** accessibility:  
- Screen reader announces: "Search input, enter filename or partial name"  
- ARIA label: `aria-label="Search files and folders"`  
- Keyboard navigation fully supported  
- High contrast mode compatible  

**Prerequisites:** Story 2.1 (Core Search Engine)  

**Technical Notes:**  
- Use QLineEdit (Qt) or ttk.Entry (Tkinter) with custom styling  
- Implement search debouncing: wait 300ms after typing before auto-search (if implemented)  
- Sanitize input to prevent regex injection if using regex matching  
- Store search history in config file, not memory (persist across restarts)  
- Consider implementing fuzzy search matching in future (Levenshtein distance)  
- Add input validation: empty query shows friendly error instead of crashing  

---

### Story 2.3: Implement Directory Selection Controls

**As a** user,  
**I want** to specify which directory to search in,  
**So that** I can narrow my search to relevant locations.

**Acceptance Criteria:**  

**Given** the search interface  
**When** I look for directory selection controls  
**Then** I should see:  
- Text input field showing current search directory path  
- Browse button (labeled "Browse..." or with folder icon)  
- Default directory: user's home directory (`~` or `%USERPROFILE%`)  
- Recently used directories dropdown (last 5 directories)  

**And** directory text input should:  
- Display full absolute path (not relative)  
- Support manual path entry with validation  
- Auto-complete common paths (home, documents, desktop)  
- Show error state for invalid paths (red border, tooltip: "Directory does not exist")  
- Accept drag-and-drop of folders from file manager  
- Be editable but also show read-only view during search  

**And** browse button should:  
- Open native file browser dialog when clicked  
- Dialog title: "Select Search Directory"  
- Default to current directory in text field  
- Show only directories (not files)  
- Allow creating new folder (platform-dependent)  
- Return selected path to text field  

**And** recently used directories:  
- Store in configuration file (persist across sessions)  
- Show as dropdown when clicking arrow or right-clicking text field  
- Display friendly names: `/home/user/Documents` → "Documents"  
- Maximum 5 entries, ordered by most recent  
- Clear history option in context menu  

**And** keyboard shortcuts:  
- **Ctrl+O:** Open browse dialog (standard "open" shortcut)  
- **Ctrl+D:** Focus directory text field  
- **Escape:** Close browse dialog without selection  

**And** the directory should:  
- Validate existence before search starts  
- Check read permissions and show error if denied  
- Support network paths (UNC on Windows, NFS/SMB on Linux/Mac)  
- Expand user shortcuts: `~`, `%USERPROFILE%`, `$HOME`  
- Handle path separators correctly across platforms  

**Prerequisites:** Story 2.2 (Search Input Interface)  

**Technical Notes:**  
- Use QFileDialog (Qt) or tkinter.filedialog for native browser  
- Validate directory using `os.path.isdir()` and `os.access(path, os.R_OK)`  
- Store recent directories list in config file under `recent_directories` key  
- Implement path normalization using `os.path.normpath()` and `os.path.expanduser()`  
- For drag-and-drop: accept `text/uri-list` MIME type and convert to path  
- Consider adding favorite directories feature (bookmarks) in growth phase  
- Add validation: warn if directory contains >100K files (performance impact)  

---

### Story 2.4: Add Search Initiation and Control

**As a** user,  
**I want** clear controls to start, stop, and monitor searches,  
**So that** I have full control over the search operation.

**Acceptance Criteria:**  

**Given** search query and directory are specified  
**When** I initiate a search  
**Then** I should see:  
- **Search button:** Labeled "Search" or with magnifying glass icon  
  - Position: Right of search input field  
  - Size: 80px wide, same height as input (32px)  
  - Color: Primary action color (blue/green)  
  - Disabled state: Grayed out when query is empty  
  - Changes to "Stop" during active search  

**And** search initiation methods:  
- Clicking Search button  
- Pressing Enter key in search input field  
- Pressing Enter key in directory field (if focused)  
- Automatic search after 500ms of typing (configurable, can be disabled)  

**And** stop functionality:  
- **Stop button:** Appears in place of Search button during active search  
- Clicking stops search immediately  
- Keyboard shortcut: **Escape** key stops search  
- Search stops gracefully, showing results found so far  
- Stop button label: "Stop" with square icon or red color  

**And** search state indicators:  
- Button state changes (Search → Stop → Search)  
- Search input disabled during search (prevents modification)  
- Directory selector disabled during search  
- Cursor changes to wait cursor (hourglass/spinner) during search  
- Status bar shows: "Searching in {directory}..." with animated ellipsis  

**And** search completion:  
- Button returns to "Search" state  
- Input fields re-enabled  
- Cursor returns to normal  
- Status shows: "Found {N} results in {time}s"  
- If stopped early: "Search stopped. Found {N} results before stopping."  
- If error occurs: "Search failed: {error_message}"  

**And** keyboard shortcuts:  
- **Ctrl+Enter:** Start search (alternative to Enter)  
- **Escape:** Stop search (if running) or clear input (if idle)  
- **Ctrl+S:** Focus search button (mnemonic)  

**Prerequisites:** Stories 2.2 and 2.3  

**Technical Notes:**  
- Implement search as background thread using `QThread` (Qt) or `threading.Thread`  
- Use thread-safe signals to communicate between search thread and UI  
- Disable UI controls during search to prevent race conditions  
- Store search state in SearchState enum: IDLE, RUNNING, STOPPING, COMPLETED, ERROR  
- Add search queue: if user starts new search while one is running, stop current and start new  
- Implement search cancellation using thread-safe flag checked during traversal  
- Consider adding pause/resume functionality for future growth feature  

---

### Story 2.5: Add Progress Indication During Search

**As a** user,  
**I want** visual feedback during search operations,  
**So that** I know the application is working and can estimate remaining time.

**Acceptance Criteria:**  

**Given** an active search operation  
**When** the search is in progress  
**Then** I should see:  

1. **Progress Bar:**  
   - Horizontal bar below search controls  
   - Indeterminate mode (pulsing) when total file count unknown  
   - Determinate mode (0-100%) when directory size pre-scanned  
   - Color: Primary theme color (blue)  
   - Height: 6px (thin, unobtrusive)  
   - Smooth animation, not jerky  

2. **Progress Text:**  
   - Format: "Scanning {N} files... | Found {M} matches"  
   - Updates every 200ms (not on every file to avoid UI lag)  
   - Shows current directory being scanned (truncated if long)  
   - Estimates remaining time if possible: "About {time} remaining"  
   - If stopped: "Search stopped at {N} files scanned"  

3. **Spinner/Activity Indicator:**  
   - Animated icon next to progress text  
   - Rotating circle or dots animation  
   - Stops when search completes  
   - Different icon for error state (red X)  

4. **File Scan Counter:**  
   - Incremental count of files scanned  
   - Format: "12,345 files scanned" (with thousands separator)  
   - Updates in batches (every 100 files) for performance  
   - Shows final count: "Search completed: {N} files scanned"  

**And** progress should be:  
- Accurate within ±10% if determinate mode  
- Responsive (updates don't block search thread)  
- Visible within 200ms of search starting  
- Hidden when search completes (smooth fade out)  

**And** performance considerations:  
- Progress updates don't significantly impact search speed (<5% overhead)  
- UI updates throttled to 5-10 per second maximum  
- Progress callback from search engine to UI uses thread-safe queue  
- Counter variables use atomic operations or locks  

**And** edge cases:  
- Very fast searches (<500ms): progress may not appear (acceptable)  
- Very slow directories (network drives): show "Scanning may take a while..."  
- Permission errors: show "Skipping inaccessible directory: {path}"  
- Symlink loops: show "Detected circular reference, skipping"  

**Prerequisites:** Story 2.4 (Search Initiation)  

**Technical Notes:**  
- Implement progress callback in search engine: `progress_callback(files_scanned, current_dir)`  
- Use `collections.deque` for thread-safe progress message queue  
- Calculate progress percentage: `(files_scanned / estimated_total_files) * 100`  
- Estimate total files using quick pre-scan or cached directory stats  
- For indeterminate progress: use `QProgressBar.setRange(0, 0)` (Qt) or simple spinner  
- Add progress throttling: only update UI if 100ms has passed since last update  
- Consider showing directory tree depth: "Scanning level 3 of 5"  
- Use platform-native progress indicators if available (macOS determinate progress)  

---

### Story 2.6: Add Search Status Display

**As a** user,  
**I want** clear status information about search results,  
**So that** I understand what was found and can adjust my query if needed.

**Acceptance Criteria:**  

**Given** a completed search operation  
**When** I view the status area  
**Then** I should see:  

1. **Results Count:**  
   - Prominent display: "{N} files found"  
   - Format: Large number with thousands separator  
   - Color: Green if results found, orange if zero, red if error  
   - Position: Top of results pane or status bar  
   - Updates in real-time as results stream in  

2. **Search Summary:**  
   - Format: "Found {N} matches in {directory}"  
   - Shows search duration: "Search completed in {time}s"  
   - Shows search query: "for '{query}'"  
   - Example: "Found 42 matches in /home/user/Documents for 'report' (0.8s)"  

3. **Zero Results State:**  
   - Friendly message: "No files found matching '{query}'"  
   - Suggestions: "Try a broader search term or different directory"  
   - Tips: "Check if 'Include hidden files' is enabled if searching for hidden files"  
   - Visual: Magnifying glass icon with question mark  

4. **Error States:**  
   - Directory not found: "Error: Directory '/invalid/path' does not exist"  
   - Permission denied: "Error: Permission denied for '/restricted/path'"  
   - Search failed: "Error: Search failed: {error_message}"  
   - Recovery suggestion: "Please select a different directory and try again"  

5. **Status Bar (persistent at bottom):**  
   - Ready state: "Ready"  
   - Searching: "Searching in {directory}..."  
   - Completed: "Found {N} results in {time}s"  
   - Error: "Error: {message}"  
   - Shows current time, line/column (if applicable)  

**And** status should update:  
- When search starts (clear previous results count)  
- As results stream in (increment counter)  
- When search completes (show final count and time)  
- When search is stopped (show partial results message)  
- When error occurs (show error message)  

**And** status persistence:  
- Last search summary remains visible until next search  
- Results count stays visible when browsing results  
- Error messages persist until user dismisses or starts new search  
- Status bar always visible showing application state  

**Prerequisites:** Story 2.5 (Progress Indication)  

**Technical Notes:**  
- Implement status update signals from search engine to UI  
- Use thread-safe counter for results found (atomic increment)  
- Format numbers using `locale.format_string()` for thousands separators  
- Store last search summary in config for persistence across restarts  
- Add status history/log in debug mode (store last 100 status messages)  
- Consider adding audio notification when search completes (configurable)  
- Status messages should be localized (use translation strings)  
- Add copy-to-clipboard functionality for status messages (right-click)  

---

## Epic 3: Results Management

Enable effective viewing and interaction with search results

### Story 3.1: Implement Results List Display

**As a** user,  
**I want** search results displayed in a clean, scrollable list,  
**So that** I can browse through found files and folders efficiently.

**Acceptance Criteria:**  

**Given** search results are available  
**When** I view the results pane  
**Then** I should see:  

1. **Results List Component:**  
   - Scrollable list occupying bottom 70% of window  
   - Virtual scrolling for performance (renders only visible items)  
   - Minimum 10 items visible without scrolling (adjustable height)  
   - Smooth scrolling with mouse wheel and touchpad gestures  
   - Scrollbar appears when content exceeds viewport  

2. **Result Item Display (each row shows):**  
   - **File name:** Bold text, primary color, left-aligned  
     - Truncated with ellipsis if too long (max 80 characters)  
     - Shows full name on hover in tooltip  
   - **Full path:** Smaller text (11px), gray color, below file name  
     - Truncated from left for long paths: `.../parent/filename.ext`  
     - Full path in tooltip on hover  
   - **File size:** Right-aligned, formatted (e.g., "2.4 MB", "15 KB", "1.2 GB")  
     - Uses 1024-based binary prefixes (KiB, MiB, GiB)  
   - **File type:** Icon or small label (e.g., 📄, 📁, 📷, 📽️)  
     - Determined by extension: .txt, .pdf, .jpg, .mp4, etc.  
     - Default icon for unknown types  
   - **Modified date:** "Modified: {date}" in subtext (if space available)  
     - Format: "Jan 15, 2024" or "15/01/2024" based on locale  

3. **List Behavior:**  
   - Items selectable (single selection by default)  
   - Highlighted background for selected item (blue/light blue)  
   - Hover effect (light gray background) for better UX  
   - Keyboard navigation: Up/Down arrows, Page Up/Down, Home/End  
   - Selection persists when sorting (maintains selected item)  

4. **Empty State:**  
   - Before first search: "Enter a search term to begin"  
   - During search: "Searching..." with spinner  
   - No results: "No files found" with magnifying glass icon  
   - Friendly messaging with suggestions  

5. **Performance Requirements:**  
   - Renders 1,000 results in under 100ms  
   - Smooth scrolling at 60fps with 10,000 results  
   - Memory efficient: doesn't load all file metadata at once  
   - Virtual scrolling loads items on-demand as user scrolls  

**And** the results list should:  
- Update in real-time as search results stream in  
- Maintain scroll position when new results added  
- Auto-scroll to first result when search completes (configurable)  
- Clear previous results when new search starts  
- Show "Loading more results..." at bottom if incremental loading  

**Prerequisites:** Story 2.1 (Core Search Engine)  

**Technical Notes:**  
- Use QListView with custom model (Qt) or ttk.Treeview (Tkinter)  
- Implement virtual scrolling: only create widgets for visible items (+ buffer)  
- Use `os.scandir()` to get file stats in one system call  
- Cache file icons by extension to avoid repeated lookups  
- Implement lazy loading: load file metadata (size, date) when item becomes visible  
- Consider using `QStandardItemModel` with `QSortFilterProxyModel` for sorting  
- For very large result sets (>10K), implement pagination or infinite scroll  
- Add accessibility: screen reader announces "Result {N} of {Total}: {filename}"  
- Use platform-native file icons via `QFileIconProvider` (Qt) or extract system icons  

---

### Story 3.2: Implement Search Result Highlighting

**As a** user,  
**I want** matching text highlighted in search results,  
**So that** I can quickly see why each file matched my query.

**Acceptance Criteria:**  

**Given** search results are displayed  
**When** I view each result  
**Then** matching text in filenames should be highlighted:  

1. **Highlight Appearance:**  
   - Matching substring shown in **bold** text  
   - Background color: yellow (#FFFF99) or accent color (configurable)  
   - Case-insensitive matching (Query="report" matches "Report.pdf", "MyReport.txt")  
   - Partial matching: "rep" matches "report", "reputation", "good_rep"  
   - Highlight all occurrences in filename if multiple matches  

2. **Highlight Logic:**  
   - Highlights in file name only (not path, not extension)  
   - Preserves original case in display ("Report" not "report")  
   - Works with wildcard patterns: query="*report*" highlights "report" portion  
   - Works with special characters in query (escapes regex metacharacters)  
   - No highlight if query is empty or only wildcards  

3. **Examples:**  
   - Query: "report" → File: "MonthlyReport.pdf" → Shows: "Monthly**report**.pdf"  
   - Query: "test" → File: "test_document.txt" → Shows: "**test**_document.txt"  
   - Query: "file" → File: "MyFile.txt" → Shows: "My**File**.txt" (case-insensitive)  
   - Query: "doc" → File: "doc_document.docx" → Shows: "**doc**_**doc**ument.docx"  

4. **Performance:**  
   - Highlighting applied in under 10ms per 100 results  
   - Doesn't block UI rendering  
   - Works with virtual scrolling (highlights only visible items)  
   - No highlight if search completes in under 200ms (fast enough to not need it)  

5. **Visual Options:**  
   - Configurable highlight color in settings  
   - Option to disable highlighting (performance on very slow systems)  
   - High contrast mode uses outline instead of background color  
   - Dark mode uses lighter highlight color  

**And** the highlight should:  
- Update dynamically if query changes (requires re-search)  
- Work with Unicode characters and international filenames  
- Handle regex special characters safely (escape before highlighting)  
- Not break text selection or copying  
- Be visible in both light and dark themes  

**Prerequisites:** Story 3.1 (Results List Display)  

**Technical Notes:**  
- Use HTML-like rich text formatting if supported by UI toolkit  
- Qt: Use `QTextCharFormat` with background color and font weight  
- Tkinter: Use Text widget tags with `tag_config()` for highlighting  
- Implement safe highlighting: escape regex metacharacters before applying  
- Use `re.IGNORECASE` flag for case-insensitive matching  
- For multiple matches: use `re.finditer()` to find all occurrences  
- Consider using `difflib` for fuzzy matching highlight in future  
- Cache highlighted text to avoid re-computing when scrolling  
- Add option to highlight in path as well as filename (configurable)  
- Test with edge cases: query=".", query="*", query="file[1]"  

---

### Story 3.3: Implement Results Sorting Functionality

**As a** user,  
**I want** to sort search results by different criteria,  
**So that** I can find the most relevant files quickly.

**Acceptance Criteria:**  

**Given** search results are displayed  
**When** I interact with sorting controls  
**Then** I should be able to sort by:  

1. **Sort Options (clickable column headers or dropdown):**  
   - **Name:** Alphabetical by filename (A-Z, Z-A)  
   - **Path:** Alphabetical by full path  
   - **Size:** Numerical by file size (smallest to largest, largest to smallest)  
   - **Date Modified:** Chronological by modification time (newest to oldest, oldest to newest)  
   - **Type:** By file extension group (folders first, then by extension)  
   - **Relevance:** By match quality (exact match > starts with > contains > ends with)  

2. **Sort Controls:**  
   - Column headers clickable in results list (if using table view)  
   - Or dropdown selector: "Sort by: [Name ▼]"  
   - Or toolbar buttons with sort icons  
   - Current sort indicated with arrow: ↑ for ascending, ↓ for descending  
   - Default sort: Name ascending (A-Z)  

3. **Sort Behavior:**  
   - Sorting applies to current results instantly (no re-search)  
   - Maintains selection (selected item stays selected after sort)  
   - Scroll position adjusted to keep selected item visible  
   - Sort state persists across searches (configurable)  
   - Sort indicator visible in UI showing current sort field and direction  

4. **Sort Implementation Details:**  
   - **Name sort:** Case-insensitive alphabetical using `str.lower()`  
     - Natural sort: "file1.txt", "file2.txt", "file10.txt" (not "file1", "file10", "file2")  
     - Use `natsort` library or custom key function  
   - **Size sort:** Numerical by bytes (intelligent handling of folders vs files)  
     - Folders can be sorted by size (recursive calculation) or always first  
   - **Date sort:** By `st_mtime` (modification time) from file stats  
     - Format displayed dates by locale  
   - **Type sort:** Group by extension, folders first, then alphabetical by ext  
   - **Relevance sort:** Calculate match score:  
     - Exact match: 100 points  
     - Starts with query: 75 points  
     - Contains query: 50 points  
     - Ends with query: 25 points  

5. **Performance:**  
   - Sorts 10,000 results in under 200ms  
   - Uses stable sort to maintain relative order of equal elements  
   - Sorting done in background thread for very large result sets (>50K)  
   - Virtual scrolling re-renders only visible items after sort  

**And** sorting should:  
- Work with virtual scrolling and incremental loading  
- Update URL/hash if browser-based (not applicable for desktop)  
- Be accessible: screen reader announces "Sorted by name, ascending"  
- Support keyboard: Ctrl+1-6 for different sort options  
- Show sort order in tooltip: "Click to sort by size (largest first)"  

**Prerequisites:** Story 3.1 (Results List Display)  

**Technical Notes:**  
- Use `sorted()` with custom key functions for each sort type  
- Implement natural sorting: `natsort.natsorted()` or custom regex-based key  
- For size sort: `key=lambda x: x.size` (folders size = 0 or calculated)  
- For date sort: `key=lambda x: x.modified_time` (timestamp)  
- Cache sort results to avoid re-sorting when switching back  
- Use `QSortFilterProxyModel` (Qt) for model-based sorting  
- Consider adding grouped view: folders separated from files  
- Add secondary sort: "Sort by type, then by name"  
- Persist sort preference in config: `default_sort_field` and `default_sort_order`  

---

### Story 3.4: Implement Double-Click to Open Files

**As a** user,  
**I want** to double-click a search result to open it,  
**So that** I can quickly access the files I find.

**Acceptance Criteria:**  

**Given** search results are displayed  
**When** I double-click a file result  
**Then** the file should open with the system's default application  

**And** the open operation should:  
- Use native OS file opening mechanism:  
  - **Windows:** `os.startfile(path)`  
  - **macOS:** `subprocess.call(['open', path])`  
  - **Linux:** `subprocess.call(['xdg-open', path])`  
  - **Cross-platform fallback:** `QDesktopServices.openUrl(QUrl.fromLocalFile(path))` (Qt)  

- Handle different file types correctly:  
  - Documents (.txt, .pdf, .docx) → Open in default viewer/editor  
  - Images (.jpg, .png, .gif) → Open in default image viewer  
  - Videos (.mp4, .avi) → Open in default media player  
  - Folders → Open in system file manager  
  - Executables (.exe, .sh) → Show warning: "This is an executable file. Open anyway?"  

- Provide visual feedback:  
  - Brief highlight flash when double-clicked  
  - Cursor changes to pointer hand on hover  
  - Status bar shows: "Opening: {filename}..."  
  - If successful: "Opened: {filename}"  
  - If failed: "Failed to open: {error_message}"  

- Support keyboard activation:  
  - **Enter key:** Opens selected file (same as double-click)  
  - **Ctrl+O:** Opens selected file (mnemonic for Open)  
  - **Spacebar:** Quick preview (if supported by OS)  

- Handle errors gracefully:  
  - File not found: Show error dialog "File no longer exists: {path}"  
  - No default application: Show "No application associated with this file type"  
  - Permission denied: Show "Permission denied: {path}"  
  - Offer to open containing folder as fallback  

**And** double-click behavior:  
- Works on files and folders  
- Single-click selects item (doesn't open)  
- Double-click speed follows system setting (detected from OS)  
- Disabled during search (results not yet stable)  
- Works with selected item if multiple items selected (opens first)  

**And** security considerations:  
- Confirm before opening executable files (.exe, .bat, .sh)  
- Show warning for files from untrusted locations (downloads folder)  
- Log opened files for user reference (privacy-conscious, can disable)  
- Never open files automatically without user action  

**Prerequisites:** Story 3.1 (Results List Display)  

**Technical Notes:**  
- Use `QAbstractItemView.doubleClicked` signal (Qt) or bind to double-click event (Tkinter)  
- Implement platform detection: `sys.platform` ('win32', 'darwin', 'linux')  
- For security: maintain whitelist of safe file types, blacklist dangerous ones  
- Add "Always open files of this type" option in context menu (configurable)  
- Consider sandboxing: open files in read-only mode where possible  
- Add MRU (Most Recently Used) list: store last 10 opened files in config  
- Implement async file open: doesn't block UI while application launches  
- Test with Unicode filenames and paths containing spaces  
- Add drag-and-drop from results list to other applications  

---

### Story 3.5: Implement Right-Click Context Menu

**As a** user,  
**I want** a context menu with file operations when I right-click a result,  
**So that** I can perform various actions on found files.

**Acceptance Criteria:**  

**Given** search results are displayed  
**When** I right-click on a file or folder result  
**Then** a context menu should appear with the following options:  

1. **Open** (default action, bold)  
   - Label: "Open" or "Open with Default Application"  
   - Shortcut: Double-click or Enter key  
   - Icon: Arrow or application icon  
   - Opens file with system default (same as double-click)  

2. **Open With...**  
   - Submenu showing list of applications that can open this file type  
   - Applications detected from OS registry/file associations  
   - Option: "Choose another application..." to browse for app  
   - Icon: Dropdown arrow or application list icon  

3. **Open Containing Folder**  
   - Label: "Open Containing Folder" or "Show in Folder"  
   - Shortcut: **Ctrl+Shift+O**  
   - Icon: Folder icon  
   - Opens parent directory in system file manager  
   - Selects/highlight the file within that folder  

4. **Copy Path**  
   - Label: "Copy Full Path to Clipboard"  
   - Shortcut: **Ctrl+Shift+C**  
   - Icon: Clipboard icon  
   - Copies absolute path as text  
   - Shows tooltip: "Path copied to clipboard"  

5. **Copy File**  
   - Label: "Copy File"  
   - Shortcut: **Ctrl+C**  
   - Icon: Copy icon  
   - Copies file to clipboard (can paste in file manager)  
   - Shows: "File copied to clipboard"  

6. **Properties**  
   - Label: "Properties" or "File Info"  
   - Shortcut: **Alt+Enter**  
   - Icon: Info icon (i)  
   - Opens dialog showing:  
     - File name, path, size, type  
     - Modified date, created date, accessed date  
     - Permissions (read/write/execute)  
     - Checksum/hash (MD5, SHA256) - calculate on demand  

7. **Delete**  
   - Label: "Delete" or "Move to Trash/Recycle Bin"  
   - Shortcut: **Delete** key  
   - Icon: Trash can icon  
   - Shows confirmation dialog: "Move {filename} to trash?"  
   - Moves to system trash (recoverable), not permanent delete  
   - Option: **Shift+Delete** for permanent delete (with confirmation)  

8. **Rename**  
   - Label: "Rename"  
   - Shortcut: **F2** key  
   - Icon: Pencil/edit icon  
   - Enables inline editing of filename  
   - Validates new name (no invalid characters, not duplicate)  
   - Updates result list after rename  

**And** context menu should:  
- Appear at mouse cursor position  
- Close when clicking outside or pressing Escape  
- Show keyboard shortcuts for each action  
- Disable options that aren't applicable (e.g., "Open With..." for folders)  
- Support keyboard navigation: Up/Down arrows, Enter to select  
- Be accessible: screen reader announces menu items  

**And** for multiple selected items:  
- Show count: "3 files selected"  
- Actions apply to all selected items where appropriate  
- "Open" opens all selected files (with warning if >5 files)  
- "Copy Path" copies all paths (one per line)  
- "Delete" shows: "Move 3 files to trash?"  

**Prerequisites:** Story 3.4 (Double-Click to Open)  

**Technical Notes:**  
- Use `QMenu` and `QAction` (Qt) or `tkinter.Menu` for context menu  
- Implement platform-native context menu appearance  
- For "Open With...": use Windows registry, macOS Launch Services, Linux .desktop files  
- Use `send2trash` library for cross-platform move to trash  
- Implement clipboard operations using `pyperclip` or Qt clipboard  
- For properties dialog: use `QFileInfo` to get file metadata  
- Add "Add to favorites" option if favorites feature implemented  
- Consider adding custom plugin actions to context menu (extensibility)  
- Test with long paths in context menu (truncation)  
- Add icons to menu items for better visual scanning (use native icons where possible)  

---

### Story 3.6: Implement "Open Containing Folder" Functionality

**As a** user,  
**I want** to open the containing folder of a search result,  
**So that** I can see the file in context and work with related files.

**Acceptance Criteria:**  

**Given** a search result is selected  
**When** I choose "Open Containing Folder"  
**Then** the parent directory should open in the system file manager  

**And** the operation should:  
- Open folder and select/highlight the specific file:  
  - **Windows:** `explorer /select,"C:\path\to\file.txt"`  
  - **macOS:** `open -R /path/to/file.txt` (Reveal in Finder)  
  - **Linux:** `nautilus --select /path/to/file.txt` (GNOME) or `dolphin --select /path/to/file.txt` (KDE) or `xdg-open /path/to/folder` (fallback)  
  - **Cross-platform:** Open folder, then try to select file (best effort)  

- Be accessible via multiple methods:  
  - Context menu: "Open Containing Folder" (Story 3.5)  
  - Keyboard shortcut: **Ctrl+Shift+O**  
  - Toolbar button (if toolbar implemented)  
  - Double-click on path text in result item  

- Provide visual feedback:  
  - Status bar: "Opening containing folder for {filename}..."  
  - Cursor: Wait cursor during operation  
  - Success: "Opened folder for {filename}"  
  - Error: "Failed to open folder: {error_message}"  

- Handle special cases:  
  - **Folders:** If result is a folder, open that folder (not parent)  
  - **Deleted files:** Show error "File no longer exists"  
  - **Permission denied:** Show error "Permission denied for {folder}"  
  - **Network paths:** Open with appropriate handler for network locations  

**And** folder should open:  
- Using native file manager (Explorer, Finder, Nautilus, Dolphin, etc.)  
- With the file selected/highlighted when possible  
- In foreground (activate window)  
- Within 1 second for local drives  
- With error handling for unavailable network locations  

**And** keyboard workflow:  
- **Tab** to navigate to results list  
- **Arrow keys** to select file  
- **Ctrl+Shift+O** to open containing folder  
- Works with single or multiple selected items (opens folder for first selected)  

**Prerequisites:** Story 3.5 (Context Menu)  

**Technical Notes:**  
- Implement platform detection and appropriate command for each OS  
- For Linux: detect desktop environment (GNOME, KDE, XFCE) and use appropriate file manager  
- Use `subprocess.Popen()` to open without blocking UI  
- Add error handling for missing file managers (fallback to `xdg-open`)  
- Consider adding "Open in Terminal" option for developers (open folder in terminal)  
- Test with paths containing spaces, Unicode characters, and special symbols  
- Add to recently opened folders list (like recent directories)  
- For multiple selection: open folder containing first selected item  
- Implement timeout: if folder doesn't open within 5 seconds, show error  

---

## FR Coverage Matrix

| Functional Requirement | Description | Epic | Story |
|------------------------|-------------|------|-------|
| **FR1** | Users can enter search terms | Epic 2 | Story 2.2 (Search Input) |
| **FR2** | Users can specify starting directory | Epic 2 | Story 2.3 (Directory Selection) |
| **FR3** | Initiate search with Enter or button | Epic 2 | Story 2.4 (Search Initiation) |
| **FR4** | Partial filename matching | Epic 2 | Story 2.1 (Core Search Engine) |
| **FR5** | Results within 2 seconds | Epic 2 | Story 2.1 (Performance Optimization) |
| **FR6** | Results in clean, scrollable list | Epic 3 | Story 3.1 (Results List Display) |
| **FR7** | Show filename, path, and size | Epic 3 | Story 3.1 (Results List Display) |
| **FR8** | Highlight matching text | Epic 3 | Story 3.2 (Result Highlighting) |
| **FR9** | Sort results by name, date, size | Epic 3 | Story 3.3 (Results Sorting) |
| **FR10** | Double-click to open files | Epic 3 | Story 3.4 (Double-Click to Open) |
| **FR11** | Right-click context menu | Epic 3 | Story 3.5 (Context Menu) |
| **FR12** | Open containing folder | Epic 3 | Story 3.6 (Open Containing Folder) |
| **FR13** | Minimal GUI with search input | Epic 2 | Story 2.2 (Search Input Interface) |
| **FR14** | Directory selection controls | Epic 2 | Story 2.3 (Directory Selection) |
| **FR15** | Progress indicator | Epic 2 | Story 2.5 (Progress Indication) |
| **FR16** | Status display | Epic 2 | Story 2.6 (Status Display) |
| **FR17** | Modular code structure | Epic 1 | Story 1.2 (Modular Structure) |
| **FR18** | Configuration file | Epic 1 | Story 1.3 (Configuration System) |
| **FR19** | Plugin architecture | Epic 1 | Story 1.4 (Plugin Architecture) |

**Coverage Validation:** ✓ All 19 FRs covered by at least one story  

---

## Summary

**Total Epics:** 3  
**Total Stories:** 10  
**Project Type:** Desktop app (low complexity)  
**MVP Boundary:** All 19 functional requirements included in MVP  
**Estimated Implementation Order:** Epic 1 → Epic 2 → Epic 3  

**Story Sizing Assessment:**  
- All stories sized for single-session completion (4-8 hours each)  
- Vertically sliced (each delivers complete user value)  
- No forward dependencies (only backward references)  
- Clear acceptance criteria with BDD format  
- Technical notes provide implementation guidance  

**Key Implementation Highlights:**  
- **Epic 1 (Foundation):** Sets up extensible architecture for future enhancements  
- **Epic 2 (Search):** Core search functionality with performance optimization  
- **Epic 3 (Results):** Rich interaction with results (sorting, opening, context menu)  

**Domain Considerations Addressed:**  
- Cross-platform compatibility (Windows, macOS, Linux)  
- Performance requirements (<2s search, <100MB memory)  
- Accessibility (keyboard navigation, screen readers)  
- Security (read-only access, safe file opening)  
- Extensibility (plugin architecture for future features)  

---

_For implementation: Use the `create-story` workflow to generate individual story implementation plans from this epic breakdown._  

_This document will be updated after UX Design and Architecture workflows to incorporate interaction details and technical decisions._

