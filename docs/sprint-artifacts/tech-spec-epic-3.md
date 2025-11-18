# Epic Technical Specification: Results Management

Date: 2025-11-16
Author: Matt
Epic ID: epic-3
Status: Draft

---

## Overview

Epic 3 implements comprehensive search results management functionality, enabling users to effectively view, sort, and interact with search results. This epic builds upon the core search engine (Epic 2) to provide a rich results display interface with highlighting, sorting, and file operations capabilities.

The epic addresses functional requirements FR6-FR12, delivering a clean scrollable results list with filename/path/size information, text highlighting for matched terms, multi-criteria sorting options, and comprehensive file operations including double-click to open, right-click context menu, and open containing folder functionality.

## Objectives and Scope

**In Scope:**
- Results list display with virtual scrolling for performance
- Search result highlighting with configurable colors
- Multi-criteria sorting (name, path, size, date, type, relevance)
- Double-click file opening with system default applications
- Right-click context menu with file operations
- Open containing folder functionality
- Cross-platform file system integration
- Performance optimization for large result sets (10K+ files)

**Out of Scope:**
- File content search and preview
- Advanced filtering beyond sorting
- Batch file operations (multiple file selection)
- File modification operations (delete, rename)
- Search result persistence across sessions
- Export functionality for results

## System Architecture Alignment

This epic aligns with the established PyQt6 architecture and modular design:

**Component Integration:**
- `ui/results_view.py` - QListView with custom model for results display
- `core/file_utils.py` - File operations for opening files and folders
- `ui/main_window.py` - Context menu implementation and event handling
- `models/search_result.py` - SearchResult dataclass for uniform result format

**Architecture Constraints:**
- Maintains thread safety using Qt signals/slots for UI updates
- Preserves memory efficiency with virtual scrolling and lazy loading
- Follows plugin architecture compatibility for future extensibility
- Adheres to cross-platform compatibility requirements (Windows, macOS, Linux)
- Maintains <100MB memory usage target for large result sets

**Performance Alignment:**
- Virtual scrolling ensures 60fps with 10,000+ results
- Background threading for sorting operations on large datasets
- Lazy loading of file metadata until items become visible
- Cached file icons by extension to minimize disk I/O

## Detailed Design

### Services and Modules

| Module | Responsibilities | Inputs | Outputs | Owner |
|--------|------------------|--------|---------|-------|
| `ui/results_view.py` | Results list rendering, virtual scrolling, selection handling | SearchResult list, sort criteria | Visual list display, user interactions | UI Layer |
| `core/file_utils.py` | File opening, folder navigation, path resolution | File path, operation type | Success/failure status, opened file/folder | Core Layer |
| `ui/main_window.py` | Context menu creation, event routing, keyboard shortcuts | User actions (click, keypress) | Triggered operations, UI updates | UI Layer |
| `models/search_result.py` | Result data structure, display formatting | Raw file path | Formatted filename, path, size, date | Model Layer |

### Data Models and Contracts

**SearchResult Dataclass (Enhanced for Display):**
```python
@dataclass
class SearchResult:
    path: Path
    size: int
    modified: float
    plugin_source: Optional[str] = None
    match_score: Optional[int] = None  # For relevance sorting

    # Display formatting methods
    def get_display_name(self) -> str
    def get_display_path(self) -> str
    def get_display_size(self) -> str
    def get_display_date(self) -> str
    def get_file_type(self) -> str  # For type grouping
```

**SortCriteria Enum:**
```python
class SortCriteria(Enum):
    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    PATH_ASC = "path_asc"
    SIZE_ASC = "size_asc"
    SIZE_DESC = "size_desc"
    DATE_DESC = "date_desc"
    DATE_ASC = "date_asc"
    TYPE_ASC = "type_asc"
    RELEVANCE_DESC = "relevance_desc"
```

**ContextMenuAction Enum:**
```python
class ContextMenuAction(Enum):
    OPEN = "open"
    OPEN_WITH = "open_with"
    OPEN_FOLDER = "open_folder"
    COPY_PATH = "copy_path"
    COPY_FILE = "copy_file"
    PROPERTIES = "properties"
```

### APIs and Interfaces

**ResultsView Class Interface:**
```python
class ResultsView(QListView):
    def __init__(self, parent=None)
    def set_results(self, results: List[SearchResult])
    def clear_results(self)
    def apply_sorting(self, criteria: SortCriteria)
    def highlight_matches(self, query: str, case_sensitive: bool = False)
    def get_selected_results(self) -> List[SearchResult]
    def on_result_double_clicked(self, index: QModelIndex)
    def on_context_menu_requested(self, position: QPoint)
```

**FileUtils Class Interface:**
```python
class FileUtils:
    @staticmethod
    def open_file(path: Path) -> bool
    @staticmethod
    def open_folder(path: Path) -> bool
    @staticmethod
    def open_containing_folder(file_path: Path) -> bool
    @staticmethod
    def get_file_properties(path: Path) -> Dict[str, Any]
    @staticmethod
    def copy_path_to_clipboard(path: Path) -> bool
```

**MainWindow Integration Methods:**
```python
class MainWindow(QMainWindow):
    def on_result_double_clicked(self, result: SearchResult)
    def on_context_menu_action(self, action: ContextMenuAction, results: List[SearchResult])
    def update_results_status(self, count: int, duration: float)
    def handle_file_open_error(self, error: FileSearchError)
```

### Workflows and Sequencing

**Results Display Workflow:**
1. SearchEngine emits `result_found(Path, search_id)` signal
2. MainWindow receives signal, creates SearchResult object
3. ResultsView model appends result to list (virtual scrolling)
4. ResultsView triggers repaint for visible items only
5. Status bar updates with incremental count
6. Highlighting applied to visible items with matching text

**Sorting Workflow:**
1. User selects sort criteria from UI control
2. MainWindow validates criteria and disables results view during sort
3. Sorting performed in background thread for large datasets (>1000 items)
4. ResultsView model updates with sorted list
5. Selection state preserved and scroll position adjusted
6. ResultsView re-enabled with updated display

**File Opening Workflow:**
1. User double-clicks or selects "Open" from context menu
2. MainWindow validates file still exists and is accessible
3. FileUtils determines platform-appropriate opening method
4. Platform-specific command executed via subprocess
5. Success/failure status displayed in status bar
6. File added to MRU (Most Recently Used) list in config

**Context Menu Workflow:**
1. User right-clicks on result item
2. MainWindow determines selected items and available actions
3. Context menu built dynamically based on selection type (file/folder)
4. Menu displayed at cursor position with keyboard shortcuts shown
5. User selects action or dismisses menu
6. Selected action routed to appropriate handler method

## Non-Functional Requirements

### Performance

- **Results Rendering:** <100ms for 1,000 initial results
- **Virtual Scrolling:** 60fps maintained with 10,000+ results
- **Sorting Operations:** <200ms for 10,000 results
- **Highlighting:** <10ms per 100 visible results
- **File Opening:** <1s for local files, <3s for network files
- **Memory Usage:** <100MB for 10,000 results with metadata
- **UI Responsiveness:** No perceptible lag during result streaming

**Performance Optimization Strategies:**
- Virtual scrolling renders only visible items (+20 item buffer)
- Lazy loading defers metadata extraction until item visible
- Icon caching by file extension reduces disk I/O
- Background threading for sorting large datasets
- Throttled UI updates (max 10 updates/second during streaming)

### Security

- **File Access:** Read-only operations, no file modification capabilities
- **Path Validation:** All paths validated with `path.exists()` before access
- **Executable Warning:** Confirmation dialog before opening .exe, .bat, .sh files
- **Untrusted Locations:** Warning for files from downloads or temp directories
- **Safe Opening:** Platform-native APIs used (os.startfile, xdg-open) prevent injection
- **Plugin Isolation:** Plugin results cannot trigger file operations directly

**Security Implementation:**
```python
def validate_file_access(path: Path) -> bool:
    # Check file exists and is readable
    # Verify path is not blocked (system directories)
    # Confirm file type safety
    # Return True if safe to proceed
```

### Reliability/Availability

- **Error Recovery:** Individual file open failures don't crash application
- **Network Paths:** Graceful degradation for unavailable network locations
- **Permission Handling:** Permission denied errors logged but don't block UI
- **Stale Results:** Validation before operations, friendly errors if file moved
- **State Persistence:** Sort preferences and MRU lists saved to config

**Reliability Features:**
- Try-catch blocks around all file system operations
- User-friendly error messages with recovery suggestions
- Logging of errors for debugging without exposing to users
- Graceful handling of deleted/moved files since search

### Observability

**Logging Requirements:**
- File operations logged at INFO level: "Opening file: {path}"
- Errors logged at ERROR level with context: "Failed to open: {path}, error: {error}"
- Performance metrics at DEBUG level: "Sorted {N} results in {ms}ms"
- User actions logged for analytics: "Context menu action: {action} on {file_type}"

**Metrics Collection:**
- Results count per search
- Sort operations frequency by criteria
- File open success/failure rates by platform
- Context menu usage patterns
- Average result set size

**Monitoring Signals:**
- Application logs: `logs/filesearch.log` with rotation
- Error tracking: Custom exception types with error codes
- Performance profiling: Debug timing for critical operations
- User behavior: Config-based analytics (opt-in)

## Dependencies and Integrations

### Runtime Dependencies

| Dependency | Version | Purpose | Epic Usage |
|------------|---------|---------|------------|
| PyQt6 | 6.6.0 | GUI framework, QListView, QMenu | Core UI components |
| loguru | 0.7.2 | Structured logging | Operation logging |
| platformdirs | 3.11.0 | Cross-platform config paths | Config file location |

### Platform-Specific Integrations

**Windows Integration:**
- `os.startfile()` for default file opening
- `explorer /select,\"path\"` for folder opening with selection
- Windows registry for "Open With..." application detection
- System file icons via Win32 API

**macOS Integration:**
- `subprocess.call(['open', path])` for file opening
- `open -R path` for revealing files in Finder
- Launch Services for application detection
- Native file icons via NSWorkspace

**Linux Integration:**
- `xdg-open` for default file opening (cross-desktop)
- Desktop environment detection (GNOME, KDE, XFCE)
- File manager specific commands (nautilus, dolphin, thunar)
- MIME type detection for "Open With..." functionality

### Development Dependencies

- pytest-qt 4.2.0+ for UI testing
- pytest-mock for mocking file operations
- pre-commit for code quality checks

## Acceptance Criteria (Authoritative)

### AC1: Results List Display
**Given** search results are available from the search engine
**When** the results are displayed in the UI
**Then** the list should show:
- Filename in bold, truncated with ellipsis if exceeding 80 characters
- Full path in smaller gray text, truncated from left for long paths
- File size right-aligned with binary prefixes (KB, MB, GB)
- File type icons based on extension
- Scrollable list with virtual scrolling maintaining 60fps
- Minimum 10 items visible without scrolling

**Test:** Verify rendering of 1,000 results completes in <100ms

### AC2: Search Result Highlighting
**Given** search results with matching query terms
**When** viewing the results list
**Then** matching text in filenames should be:
- Highlighted with bold font weight
- Background color applied (yellow #FFFF99 default)
- Case-insensitive matching applied
- All occurrences highlighted if multiple matches exist
- Highlighting applied only to visible items during scrolling

**Test:** Query "report" should highlight "Monthly**report**.pdf" and "**report**_doc.txt"

### AC3: Results Sorting Functionality
**Given** a set of search results
**When** user selects sort criteria from UI controls
**Then** results should reorder instantly by:
- Name (A-Z, Z-A) with natural sorting (file1, file2, file10)
- Size (smallest to largest, largest to smallest)
- Date modified (newest to oldest, oldest to newest)
- File type (folders first, then by extension)
- Relevance (exact match > starts with > contains > ends with)

**Test:** Sort 10,000 results by size completes in <200ms, selection state preserved

---

**Implementation Status: ✅ COMPLETED 2025-11-17**

**What was implemented:**
- Core `SortEngine` class with 5 sorting algorithms (name, size, date, type, relevance)
- Natural sorting using `natsort` library for filenames
- Relevance scoring based on query position (exact > starts > contains > ends)
- UI controls: SortControls widget with dropdown and visual indicator
- Keyboard shortcuts: Ctrl+1..5 for criteria, Ctrl+R to reverse
- Configuration persistence: Sort criteria saved/restored from QSettings
- ResultsModel integration with sort_results() method
- Performance: Meets targets (<100ms for 1K names, <200ms for 10K sizes)

**Key Technical Decisions:**
- No background threading for MVP (target <1K results, single-threaded meets timing)
- Stable sort algorithms maintain relative order
- Folder detection via `path.is_dir()` not file size
- Relevance sorting requires active query (falls back to name if none)
- Selection preservation: Best-effort re-selection of same item post-sort

**Test Coverage:**
- 22 unit tests for SortEngine algorithms
- 6 integration tests for end-to-end sorting flows
- Performance tests verify timing requirements
- All tests passing

---

### AC4: Double-Click to Open Files
**Given** a file result in the search results
**When** user double-clicks on result
**Then** file should open with:
- System default application for the file type
- Platform-appropriate method (os.startfile on Windows, open on macOS, xdg-open on Linux)
- Visual feedback showing "Opening: {filename}" in status bar
- Success/failure status displayed after operation
- Executable files (.exe, .bat, .sh) show confirmation dialog before opening

**Test:** Double-click test.txt opens in default text editor, executable shows warning dialog

---

**Implementation Status: ✅ COMPLETED 2025-11-18**

**What was implemented:**
- Enhanced `file_utils.py` with `safe_open()` method supporting all platforms (Windows, macOS, Linux)
- Added Qt fallback using `QDesktopServices.openUrl()` for cross-platform compatibility
- Created comprehensive `security_manager.py` with executable detection and warning dialogs
- Enhanced `results_view.py` with double-click signal handling, keyboard Enter activation, and visual feedback
- Enhanced `main_window.py` with security dialogs, status bar updates, and MRU list management
- Added configuration support for security preferences and "always allow" decisions per file type
- Implemented comprehensive error handling with fallback to "Open Containing Folder"
- Added visual feedback: highlight flash, cursor changes, status messages with timeouts
- Disabled double-click during active search to prevent opening unstable results

**Key Technical Decisions:**
- Platform detection using `sys.platform` with specific implementations for each OS
- Security warnings for executable files (.exe, .bat, .sh, .cmd, .msi) with user preference persistence
- Qt fallback ensures compatibility across all supported platforms
- Non-blocking UI operations with status feedback and error handling
- MRU (Most Recently Used) list stores last 10 opened files in configuration
- Single-click selects without opening, double-click opens - prevents accidental opening

**Test Coverage:**
- 407 lines of unit tests for security_manager.py (24 test methods)
- 412 lines of unit tests for file_utils.py (40+ test methods covering all platforms)
- 355 lines of integration tests for end-to-end file opening workflow (12 test classes)
- Platform-specific opening mocked and tested for Windows, macOS, Linux
- Security warning dialog flow thoroughly tested
- Error handling validated for all failure scenarios
- All tests passing with >85% code coverage

**Security Implementation:**
- Executable file detection by extension and file signature
- User preferences for allowed/blocked extensions with persistence
- Security warnings with user confirmation and "Always allow" option
- Safe file opening using platform-native APIs preventing injection
- No automatic execution without explicit user action

---

### AC5: Right-Click Context Menu
**Given** search results are displayed
**When** user right-clicks on a result
**Then** a context menu should appear with options:
- Open (default, bold text)
- Open With... (submenu with applications)
- Open Containing Folder
- Copy Path to Clipboard
- Copy File to Clipboard
- Properties (file info dialog)
- Delete (with confirmation)
- Rename (inline editing)

**Test:** All menu options functional, keyboard navigation supported, screen reader accessible

### AC6: Open Containing Folder Functionality
**Given** a selected search result
**When** user chooses "Open Containing Folder"
**Then** the parent directory should open:
- In system file manager (Explorer, Finder, Nautilus/Dolphin)
- With the specific file selected/highlighted when possible
- Within 1 second for local drives
- Using platform-specific commands for selection

**Test:** Ctrl+Shift+O opens folder with file selected on all platforms

## Traceability Mapping

| AC | PRD Section | Architecture Component | API/Interface | Test Strategy |
|----|-------------|------------------------|---------------|---------------|
| AC1 | FR6, FR7 | `ui/results_view.py` | `ResultsView.set_results()` | Unit: rendering performance, Integration: virtual scrolling |
| AC2 | FR8 | `ui/results_view.py` | `ResultsView.highlight_matches()` | Unit: highlight regex, UI: visual verification |
| AC3 | FR9 | `ui/results_view.py` | `ResultsView.apply_sorting()` | Unit: sort algorithms, Performance: large dataset |
| AC4 | FR10 | `core/file_utils.py`, `core/security_manager.py` | `FileUtils.safe_open()`, `SecurityManager.check_executable()` | Integration: platform-specific, Manual: file type testing | ✅ IMPLEMENTED 2025-11-18 |
| AC5 | FR11 | `ui/main_window.py` | `MainWindow.on_context_menu()` | UI: menu functionality, Integration: action routing |
| AC6 | FR12 | `core/file_utils.py` | `FileUtils.open_containing_folder()` | Integration: platform commands, Manual: folder opening |

## Risks, Assumptions, Open Questions

### Risks

**R1: Platform Compatibility Variations**
- **Risk:** Different Linux desktop environments handle file opening inconsistently
- **Impact:** Medium - Some users may experience issues on less common DEs
- **Mitigation:** Implement fallback chain (DE-specific → xdg-open → error message)
- **Probability:** Medium (affects ~15% of Linux users on non-GNOME/KDE)

**R2: Performance with Very Large Result Sets**
- **Risk:** 100K+ results may exceed memory targets or cause UI lag
- **Impact:** Low - MVP targets 10K files, but growth feature may need 100K
- **Mitigation:** Implement incremental loading, stricter result limits, memory profiling
- **Probability:** Low (edge case for typical desktop usage)

**R3: File Icon Extraction Performance**
- **Risk:** Platform icon lookup can be slow, blocking UI thread
- **Impact:** Medium - May cause scrolling lag if not properly cached
- **Mitigation:** Aggressive caching, lazy loading, background icon fetching
- **Probability:** Medium (noticeable on Windows with certain file types)

### Assumptions

**A1: File System Access**
- **Assumption:** Application has read access to search directories
- **Validation:** Permission checks before operations, graceful error handling
- **Impact if False:** Some files won't be openable, but core functionality remains

**A2: Default Applications Configured**
- **Assumption:** Users have default applications assigned to file types
- **Validation:** Error handling for "no default application" scenarios
- **Impact if False:** Users can still use "Open With..." or open containing folder

**A3: Platform APIs Stable**
- **Assumption:** Platform file opening APIs (os.startfile, xdg-open) remain stable
- **Validation:** Fallback mechanisms and error handling for API changes
- **Impact if False:** May need updates for new OS versions

### Open Questions

**Q1: File Modification Operations**
- **Question:** Should we include delete/rename in MVP context menu?
- **Considerations:** Increases complexity, security implications, testing burden
- **Recommendation:** Defer to post-MVP, focus on read-only operations for MVP
- **Decision Needed:** Yes/No by end of Epic 3 implementation

**Q2: Search Result Persistence**
- **Question:** Should results persist across application restarts?
- **Considerations:** Useful for recent searches, but increases complexity
- **Recommendation:** Implement basic MRU list, defer full persistence
- **Decision Needed:** Scope clarification before Story 3.1 implementation

**Q3: Multi-Selection Operations**
- **Question:** Should context menu actions support multiple selected files?
- **Considerations:** Batch operations valuable but complex error handling
- **Recommendation:** Implement for simple actions (copy path, open folder), defer others
- **Decision Needed:** Technical feasibility assessment during Story 3.5

## Test Strategy Summary

### Test Levels

**Unit Tests (pytest):**
- ResultsView rendering logic and virtual scrolling
- Sorting algorithm implementations for each criteria
- FileUtils platform detection and command generation
- SearchResult display formatting methods
- Highlight pattern matching and regex safety

**Integration Tests (pytest-qt):**
- End-to-end results display from search engine signals
- Context menu functionality and action routing
- File opening across platforms (mocked file operations)
- Sorting integration with ResultsView model updates
- Keyboard shortcut handling

**UI Tests (pytest-qt):**
- Virtual scrolling performance with large datasets
- Double-click and context menu interactions
- Visual verification of highlighting and formatting
- Accessibility features (screen reader compatibility)
- Cross-platform UI consistency

### Test Coverage Targets

- **Code Coverage:** >85% for new code in Epic 3
- **AC Coverage:** 100% of acceptance criteria tested
- **Platform Coverage:** Windows, macOS, Linux (where possible)
- **Performance Tests:** Automated benchmarks for rendering and sorting

### Critical Path Testing

1. **Happy Path:** Search → Results display → Sort → Double-click → File opens
2. **Error Path:** Search → Results → Click deleted file → Error message shown
3. **Performance Path:** Large dataset → Virtual scrolling → Sort → Memory usage <100MB
4. **Platform Path:** Same operations tested on Windows, macOS, Linux VMs

### Edge Cases

- Empty result sets and zero-results UI state
- Very long filenames and paths (OS maximum limits)
- Unicode and international characters in filenames
- Special characters in search queries affecting highlighting
- Network paths and permission-restricted directories
- Files deleted/moved since search completion
- Very large files (size display formatting)
- Symlinks and circular directory references

## Post-Review Follow-ups

### Story 3.1 Critical Issues (2025-11-17)

**Blocking Issues:**
- **SearchWorker Creation Missing**: start_search method doesn't create SearchWorker instance or connect signals, breaking search functionality completely
- **Virtual Scrolling Not Implemented**: ResultsModel doesn't implement virtual scrolling, preventing performance requirements from being met
- **Keyboard Navigation Missing**: No implementation for Up/Down, Page Up/Down, Home/End keys

**Action Items:**
1. Complete start_search method implementation with SearchWorker creation and signal connections
2. Implement proper virtual scrolling in ResultsModel for performance targets
3. Add keyboard navigation support to ResultsView
4. Configure 70% layout for ResultsView in MainWindow
5. Add auto-scroll functionality when search completes

**Impact:** Story 3.1 is BLOCKED until critical search functionality is implemented.

---

**Document Status:** Draft - Ready for Review
**Implementation Progress:**
- AC1 (Results Display): ⚠️ BLOCKED - Critical gaps in Story 3.1
- AC2 (Search Highlighting): ✅ COMPLETED 2025-11-17
- AC3 (Results Sorting): ✅ COMPLETED 2025-11-17
- AC4 (Double-Click Opening): ✅ COMPLETED 2025-11-18
- AC5 (Context Menu): 🔄 IN PROGRESS - Story 3.5 pending
- AC6 (Open Containing Folder): 🔄 IN PROGRESS - Story 3.6 pending

**Next Steps:**
1. **BLOCKED**: Address Story 3.1 critical implementation gaps (SearchWorker, virtual scrolling, keyboard navigation)
2. **COMPLETED**: Story 3.4 double-click functionality fully implemented and tested
3. Proceed to Story 3.5 (Context Menu) implementation after 3.1 unblocked
4. Set up performance benchmarking environment for virtual scrolling validation
5. Complete Stories 3.5-3.6 to finish Epic 3 implementation
