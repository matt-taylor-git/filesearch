# Story 3.3: Implement Results Sorting Functionality

Status: review

## Story

As a user,
I want to sort my search results by different criteria,
So that I can find the most relevant files more efficiently.

## Acceptance Criteria

### AC1: Sort by Name (Alphabetical)
**Given** search results are displayed in the results list
**When** user selects "Name (A-Z)" sort option
**Then** results should reorder alphabetically by filename using natural sorting (file1, file2, file10)
**And** folders should be grouped together and sorted separately from files

**Test:** Sort 1,000 mixed files/folders by name completes in <100ms

### AC2: Sort by Size
**Given** search results include files of various sizes
**When** user selects "Size" sort option (smallest to largest or largest to smallest)
**Then** results should reorder by file size in bytes
**And** folders should be placed at the top or bottom based on sort direction
**And** size display should update to show binary prefixes (KB, MB, GB)

**Test:** Sort 10,000 results by size completes in <200ms

### AC3: Sort by Date Modified
**Given** search results with various modification timestamps
**When** user selects "Date Modified" sort option (newest to oldest or oldest to newest)
**Then** results should reorder by modification timestamp
**And** display should show formatted dates (YYYY-MM-DD HH:MM)
**And** selection state should be preserved after sorting

**Test:** Sort results by date preserves selection and scroll position

### AC4: Sort by File Type
**Given** search results include multiple file types and folders
**When** user selects "File Type" sort option
**Then** results should group by type: folders first, then files sorted by extension
**And** within each group, items should be sorted alphabetically
**And** type icons should display correctly for each group

**Test:** Mixed file types sort correctly with proper grouping

### AC5: Sort by Relevance
**Given** search results from a query
**When** user selects "Relevance" sort option
**Then** results should order by match quality: exact match > starts with > contains > ends with
**And** match score should be calculated based on query position in filename
**And** most relevant files should appear at the top

**Test:** Query "report" orders "report.pdf" before "monthly_report.pdf" before "my_report.txt"

### AC6: UI Controls and User Experience
**Given** the results view is visible
**When** user interacts with sort controls
**Then** the following should be available:
- Dropdown or button group with sort criteria options
- Visual indicator showing current sort criteria and direction (ascending/descending)
- Keyboard shortcuts for quick sorting (Ctrl+1..5 for criteria, Ctrl+R to reverse)
- Sort options should be accessible from toolbar and context menu
- Sort state should persist across searches within the same session

**Test:** All UI controls functional and keyboard shortcuts work correctly

## Tasks / Subtasks

### Sorting Logic Implementation
- [ ] Create `src/filesearch/core/sort_engine.py` with `SortEngine` class
  - [ ] Implement natural sorting algorithm for filenames
  - [ ] Implement size comparison with folder handling
  - [ ] Implement date/timestamp comparison
  - [ ] Implement file type grouping and sorting
  - [ ] Implement relevance scoring algorithm
  - [ ] Add comprehensive type hints throughout
  - [ ] Write unit tests for each sorting algorithm

### UI Controls Implementation
- [ ] Enhance `src/filesearch/ui/results_view.py`
  - [ ] Add sort control widget (dropdown or button group)
  - [ ] Add visual sort indicator (arrow showing direction)
  - [ ] Implement sort control event handlers
  - [ ] Add sort options to results context menu
  - [ ] Implement keyboard shortcut handling

### Results Model Enhancement
- [ ] Enhance `src/filesearch/ui/results_view.py` ResultsModel class
  - [ ] Add sort method that accepts `SortCriteria` enum
  - [ ] Implement background threading for large datasets (>1000 items)
  - [ ] Add selection preservation during sort
  - [ ] Add scroll position preservation
  - [ ] Implement sort state management

### Integration with Main Window
- [ ] Enhance `src/filesearch/ui/main_window.py`
  - [ ] Add sort toolbar or control panel
  - [ ] Connect sort controls to ResultsView
  - [ ] Add sort state to configuration persistence
  - [ ] Implement sort indicator updates

### Configuration System Integration
- [ ] Enhance `src/filesearch/core/config_manager.py`
  - [ ] Add default sort criteria to configuration schema
  - [ ] Add sort direction persistence
  - [ ] Add sort preferences to settings dialog

### Testing
- [ ] Write unit tests for SortEngine
  - [ ] Test each sorting algorithm independently
  - [ ] Test edge cases (empty lists, single item, all identical)
  - [ ] Test natural sorting with version numbers
  - [ ] Test relevance scoring with various query patterns
- [ ] Write integration tests
  - [ ] Test end-to-end sorting from UI to results display
  - [ ] Test background threading behavior
  - [ ] Test selection and scroll preservation
  - [ ] Test configuration persistence
- [ ] Write UI tests with pytest-qt
  - [ ] Test sort control interactions
  - [ ] Test keyboard shortcuts
  - [ ] Test visual sort indicator updates

### Documentation
- [ ] Update `docs/user_guide.md` with sorting features
  - [ ] Document available sort criteria
  - [ ] Explain natural sorting behavior
  - [ ] List keyboard shortcuts
- [ ] Update `docs/sprint-artifacts/tech-spec-epic-3.md`
  - [ ] Mark AC3 as implemented
  - [ ] Update implementation status

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Sorting Architecture (from Tech Spec):**
- Background threading for sorting operations on large datasets (>1000 items)
- Thread-safe using Qt signals/slots for UI updates
- Memory efficient with in-place sorting where possible
- Performance target: <200ms for 10,000 results

**Technology Stack Alignment:**
- **PyQt6**: QListView, QThread, signals/slots for sorting operations
- **Python 3.9+**: Type hints, dataclasses for SortCriteria
- **pytest-qt**: UI testing for sort controls and interactions

**Code Quality Standards (from Story 1.1):**
- Type hints for all public methods (Python 3.9+ compatibility)
- Google-style docstrings on all modules and public functions
- Error handling using custom exception hierarchy from `core/exceptions.py`
- Structured logging with loguru
- Comprehensive unit tests with >80% coverage

**Design Patterns:**
- **Strategy Pattern**: Different sorting algorithms as strategies
- **Observer Pattern**: Sort state changes notify UI
- **Command Pattern**: Sort operations encapsulated as commands
- **Background Worker Pattern**: QThread for large dataset sorting

### Source Tree Components to Touch

**Files to Create:**
- `src/filesearch/core/sort_engine.py` - Core sorting logic
- `tests/unit/test_sort_engine.py` - Unit tests for SortEngine
- `tests/integration/test_sorting_integration.py` - Integration tests
- `tests/ui/test_sorting_controls.py` - UI tests for sort controls

**Files to Enhance:**
- `src/filesearch/ui/results_view.py` - Add sorting controls and model enhancements
- `src/filesearch/ui/main_window.py` - Integrate sort controls
- `src/filesearch/core/config_manager.py` - Add sort configuration

### Testing Standards Summary

**Framework**: pytest with pytest-qt for UI components
- Unit tests for SortEngine in `/tests/unit/`
- Integration tests for end-to-end sorting
- UI tests for sort control interactions
- Target: >85% code coverage for new code

**Test Categories:**
- **Happy path tests**: Normal sorting operations
- **Edge case tests**: Empty lists, single items, identical items
- **Performance tests**: Large dataset sorting within time targets
- **Platform tests**: Cross-platform compatibility

### Learnings from Previous Story (3-2)

**From Story 3.2 (Status: done, approved)**

- **New Services Created**:
  - `HighlightEngine` class available at `src/filesearch/utils/highlight_engine.py` - use for pattern recognition
  - `ResultsItemDelegate` enhanced at `src/filesearch/ui/results_view.py` - extend for sort indicators
  - Settings dialog tab pattern established - follow for sort preferences

- **Architectural Patterns Established**:
  - Virtual scrolling implementation pattern for performance
  - Background threading for non-UI operations
  - Configuration integration with validation
  - UI delegate pattern for custom rendering

- **Performance Optimization Patterns**:
  - Caching strategies (pattern caching in highlight engine)
  - Visible-item-only computations
  - Lazy loading deferred until necessary

- **Testing Patterns Established**:
  - 35 unit tests for highlight engine with 100% pass rate
  - 9 UI tests for results view
  - pytest-qt for event loop management
  - >80% coverage target

- **Code Quality Standards**:
  - Google-style docstrings
  - Type hints for all public methods
  - Error handling with specific exception types
  - Logging integration throughout
  - Configuration validation

[Source: docs/sprint-artifacts/stories/3-2-implement-search-result-highlighting.md]

### References

- **Architecture**: [Source: docs/architecture.md#Results-View-Performance]
- **Tech Spec**: [Source: docs/sprint-artifacts/tech-spec-epic-3.md#AC3-Results-Sorting-Functionality]
- **PRD**: [Source: docs/PRD.md#FR9-Results-Sorting]
- **Previous Story**: [Source: docs/sprint-artifacts/stories/3-2-implement-search-result-highlighting.md]

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/stories/3-3-implement-results-sorting-functionality.context.xml

### Agent Model Used

{kimi-k2-thinking}

### Debug Log References

### Completion Notes List

### File List

## Change Log

- 2025-11-17: Story drafted by SM agent
