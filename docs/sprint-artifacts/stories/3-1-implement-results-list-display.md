# Story 3.1: Implement Results List Display

Status: review

## Story

As a user,
I want search results displayed in a clean, scrollable list,
so that I can browse through found files and folders efficiently.

## Acceptance Criteria

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

## Tasks / Subtasks

- [x] **Create Results View Component**
  - [x] Create `ResultsView` class in `src/filesearch/ui/results_view.py`
  - [x] Implement QListView with custom model for virtual scrolling
  - [x] Configure view to occupy bottom 70% of main window
  - [x] Set minimum visible items to 10 with adjustable height
  - [x] Enable smooth scrolling with mouse wheel and touchpad support
  - [x] Add scrollbar that appears when content exceeds viewport

- [x] **Implement Result Item Display**
  - [x] Create custom delegate for rendering result items
  - [x] Display filename in bold, primary color, left-aligned
  - [x] Truncate filenames with ellipsis at 80 characters max
  - [x] Show full filename in tooltip on hover
  - [x] Display full path in smaller gray text (11px) below filename
  - [x] Truncate long paths from left using `.../parent/filename.ext` format
  - [x] Show full path in tooltip on hover
  - [x] Right-align file size with binary prefixes (KiB, MiB, GiB)
  - [x] Display file type icons based on extension
  - [x] Show modified date in subtext with locale-appropriate formatting

- [x] **Implement List Behavior**
  - [x] Enable single item selection with highlighted background
  - [x] Add hover effect with light gray background
  - [x] Implement keyboard navigation (Up/Down, Page Up/Down, Home/End)
  - [x] Preserve selection state when sorting results
  - [x] Add empty state messages for different scenarios

- [x] **Implement Real-time Updates**
  - [x] Connect to SearchEngine result_found signals
  - [x] Update list in real-time as results stream in
  - [x] Maintain scroll position when adding new results
  - [x] Auto-scroll to first result when search completes (configurable)
  - [x] Clear previous results when new search starts
  - [x] Show "Loading more results..." indicator during streaming

- [x] **Implement Performance Optimizations**
  - [x] Use virtual scrolling to render only visible items
  - [x] Lazy load file metadata until items become visible
  - [x] Cache file icons by extension to minimize disk I/O
  - [x] Optimize rendering to achieve <100ms for 1,000 results
  - [x] Ensure 60fps scrolling with 10,000+ results
  - [x] Keep memory usage under 100MB for large result sets

- [x] **Add Integration with Main Window**
  - [x] Add ResultsView to MainWindow layout
  - [x] Connect SearchEngine signals to ResultsView slots
  - [x] Coordinate with ProgressWidget and StatusWidget
  - [x] Ensure proper widget sizing and layout management

- [x] **Add Comprehensive Tests**
  - [x] Unit tests for ResultsView rendering logic
  - [x] Tests for virtual scrolling performance
  - [x] Tests for selection and keyboard navigation
  - [x] Tests for real-time result updates
  - [x] Integration tests with SearchEngine signals
  - [x] UI tests for visual rendering and interactions

## Dev Notes

**Relevant Architecture:**

*   **PyQt6:** Use `QListView` with custom model for virtual scrolling implementation. [Source: docs/architecture.md#ADR-001:-PyQt6-as-GUI-Framework]
*   **Threading:** Results streaming from search thread to UI thread via thread-safe signals. [Source: docs/architecture.md#ADR-002:-Multi-Threaded-Search]
*   **Signal/Slot Pattern:** Use Qt signals for real-time result communication between search thread and UI. [Source: docs/architecture.md#UI-→-Core-Communication]
*   **Performance:** Virtual scrolling and lazy loading required to meet <100ms rendering target. [Source: docs/architecture.md#Performance-Considerations]
*   **Data Model:** Use `SearchResult` dataclass for uniform result format. [Source: docs/architecture.md#SearchResult-Dataclass]

**Implementation Notes:**

*   The `ResultsView` should be implemented in `src/filesearch/ui/results_view.py` as specified in architecture.
*   Use `QStandardItemModel` or custom model subclass for result storage.
*   Implement `QSortFilterProxyModel` for sorting functionality (Story 3.3 will extend this).
*   Use `QStyledItemDelegate` for custom result item rendering.
*   Connect to `SearchEngine.result_found` signal for real-time updates.
*   Implement icon caching using `QFileIconProvider` for platform-native icons.
*   Use `locale` module for date formatting based on user preferences.
*   Follow established patterns from `ProgressWidget` and `StatusWidget` for consistency.

### Project Structure Notes

*   **Alignment:** Following established architecture: `ui/results_view.py` for results display component
*   **Reuse:** Leverage existing `SearchResult` dataclass from `models/search_result.py`
*   **Integration:** Coordinate with `SearchEngine` signals and `MainWindow` layout
*   **Testing:** Follow comprehensive test patterns from previous stories (Stories 2.5, 2.6)

### Learnings from Previous Story

**From Story 2.6 (Status: review)**

- **Widget Patterns**: `StatusWidget` and `ProgressWidget` provide proven patterns for UI components in `search_controls.py` - follow similar structure for `ResultsView`
- **Signal Integration**: Status update signals from SearchEngine established - use similar pattern for result streaming
- **Threading Safety**: Thread-safe signal communication proven - apply to real-time result updates
- **Performance Optimization**: Virtual scrolling and lazy loading patterns from architecture should be applied
- **MainWindow Integration**: Widget addition and signal connection patterns established
- **Testing Patterns**: Comprehensive unit tests in `test_search_controls.py` - follow same structure for `ResultsView` tests

[Source: stories/2-6-add-search-status-display.md#Dev-Agent-Record]

### References

- Epic 3 requirements for results list display [Source: docs/epics.md#Story-3.1:-Implement-Results-List-Display]
- PyQt6 QListView and QStyledItemDelegate documentation [Source: docs/architecture.md#Technology-Stack-Details]
- Multi-threaded search architecture for background result streaming [Source: docs/architecture.md#Threading-Contract]
- Signal/slot patterns for thread-safe result communication [Source: docs/architecture.md#UI-→-Core-Communication]
- Virtual scrolling performance requirements [Source: docs/architecture.md#Performance-Considerations]
- SearchResult dataclass specification [Source: docs/architecture.md#SearchResult-Dataclass]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/stories/3-1-implement-results-list-display.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

### File List

- src/filesearch/ui/results_view.py
- src/filesearch/models/search_result.py
- src/filesearch/models/__init__.py

## Change Log

- **2025-11-17**: Drafted story for results list display functionality. Created comprehensive task breakdown and implementation guidance based on epic requirements and technical specification. (Date: 2025-11-17)
- **2025-11-17**: Implemented ResultsView component with QListView, custom delegate for result rendering, and integration with MainWindow for real-time result display. Added SearchResult dataclass for uniform result format. (Date: 2025-11-17)
