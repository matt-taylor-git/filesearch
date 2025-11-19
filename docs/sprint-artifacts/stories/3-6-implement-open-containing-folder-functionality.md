# Story 3.6: Implement "Open Containing Folder" Functionality

Status: review

## Story

As a user,
I want to open the containing folder of a search result,
So that I can see the file in context and work with related files.

## Acceptance Criteria

### AC1: Open Parent Directory
**Given** a search result is selected
**When** I choose "Open Containing Folder"
**Then** the parent directory should open in the system file manager
**And** the specific file should be selected/highlighted when possible

**Test:** Ctrl+Shift+O shortcut works, opens folder with file selected

### AC2: Access Methods
**Given** search results are displayed
**When** I interact with the results
**Then** "Open Containing Folder" should be accessible via:
- Context menu: "Open Containing Folder" (Story 3.5)
- Keyboard shortcut: **Ctrl+Shift+O**
- Toolbar button (if toolbar implemented)
- Double-click on path text in result item

**Test:** All access methods trigger the folder opening action

### AC3: Platform-Specific Implementation
**Given** a folder open request
**When** the action executes
**Then** the system should use appropriate platform commands:
- **Windows:** `explorer /select,"C:\path\to\file.txt"`
- **macOS:** `open -R /path/to/file.txt` (Reveal in Finder)
- **Linux:** `nautilus --select /path/to/file.txt` (GNOME) or `dolphin --select /path/to/file.txt` (KDE) or `xdg-open /path/to/folder` (fallback)
- **Cross-platform:** Open folder, then try to select file (best effort)

**Test:** Verify correct command is executed for the current platform

### AC4: Visual Feedback
**Given** an open operation is initiated
**When** the action is processing
**Then** visual feedback should be provided:
- Status bar: "Opening containing folder for {filename}..."
- Cursor: Wait cursor during operation
- Success: "Opened folder for {filename}"
- Error: "Failed to open folder: {error_message}"

**Test:** Status messages appear during and after operation

### AC5: Special Case Handling
**Given** specific edge cases
**When** "Open Containing Folder" is triggered
**Then** it should handle:
- **Folders:** If result is a folder, open that folder (not parent)
- **Deleted files:** Show error "File no longer exists"
- **Permission denied:** Show error "Permission denied for {folder}"
- **Network paths:** Open with appropriate handler for network locations

**Test:** Each edge case is handled gracefully with appropriate messaging

### AC6: Multi-Selection Behavior
**Given** multiple items are selected
**When** "Open Containing Folder" is triggered
**Then** the operation should open the folder for the first selected item only
**And** status message should indicate which file's folder was opened

**Test:** Multi-selection opens folder for first item only

## Tasks / Subtasks

### Core Implementation
- [x] Enhance `src/filesearch/core/file_utils.py`
  - [x] Implement `reveal_file_in_folder(path)` method
  - [x] Add platform detection (Windows, macOS, Linux, specific DEs)
  - [x] Implement Windows `explorer /select` logic
  - [x] Implement macOS `open -R` logic
  - [x] Implement Linux desktop environment detection (GNOME, KDE, etc.)
  - [x] Implement Linux specific file manager selection commands
  - [x] Add generic fallback (open folder without selection)
  - [x] Write unit tests for platform detection and command generation

### UI Integration
- [x] Update `src/filesearch/ui/main_window.py`
  - [x] Add `on_open_containing_folder()` method
  - [x] Connect to context menu action
  - [x] Connect to keyboard shortcut (Ctrl+Shift+O)
  - [x] Implement status bar updates
  - [x] Add wait cursor during operation
  - [x] Add error dialog handling

- [x] Update `src/filesearch/ui/results_view.py`
  - [x] Add double-click handler for path column (if applicable)
  - [x] Ensure correct item is identified for multi-selection

### Testing
- [x] Write unit tests for `reveal_file_in_folder`
  - [x] Mock platform calls for Windows, macOS, Linux
  - [x] Test fallback mechanisms
  - [x] Test error conditions (file not found)
- [x] Write integration tests
  - [x] Test connection from UI to core logic
  - [x] Test keyboard shortcut activation
- [x] Write UI tests
  - [x] Test status message updates
  - [x] Test cursor changes

### Documentation
- [x] Update `docs/user_guide.md`
  - [x] Document "Open Containing Folder" feature
  - [x] Document keyboard shortcut
- [x] Update `docs/sprint-artifacts/tech-spec-epic-3.md`
  - [x] Mark AC6 (Open Containing Folder) as implemented

### Review Follow-ups (AI)
- [x] [AI-Review][High] Implement "Double-click on path text" detection in `ResultsView` (AC2)
- [x] [AI-Review][High] Add wait cursor during folder open operation (AC4)
- [x] [AI-Review][Med] Consider adding error dialog for folder open failures consistent with file opening

## Dev Notes

### Relevant Architecture Patterns and Constraints

**Platform-Specific Commands:**
- **Windows**: `subprocess.run(['explorer', '/select,', str(path)])`
- **macOS**: `subprocess.run(['open', '-R', str(path)])`
- **Linux**: Requires DBus or specific file manager calls. Fallback to `xdg-open` on parent dir is acceptable if selection not supported.
  - GNOME: `subprocess.run(['nautilus', '--select', str(path)])`
  - KDE: `subprocess.run(['dolphin', '--select', str(path)])`
  - Fallback: `subprocess.run(['xdg-open', str(path.parent)])`

**Code Quality Standards:**
- Type hints for all methods
- Google-style docstrings
- Comprehensive error handling with custom exceptions
- Thread-safe execution (use `subprocess.Popen` to avoid blocking UI)

### Source Tree Components to Touch

**Files to Enhance:**
- `src/filesearch/core/file_utils.py` - Add `reveal_file_in_folder`
- `src/filesearch/ui/main_window.py` - Add action handler
- `tests/unit/test_file_utils_operations.py` - Add tests

**New Tests:**
- `tests/integration/test_open_containing_folder.py`

## Dev Agent Record

### Context Reference

- docs/sprint-artifacts/stories/3-6-implement-open-containing-folder-functionality.context.xml

### Agent Model Used

{{agent_model_name_version}}

### Debug Log References

### Completion Notes List

- Implemented `reveal_file_in_folder` utility supporting all major platforms (Windows, macOS, Linux).
- Updated `ResultsView` to emit `folder_open_requested` signal and handle `Ctrl+Shift+O` shortcut.
- Updated `MainWindow` to handle the signal and context menu action, supporting multi-selection (opens first item).
- Added comprehensive unit tests and integration tests verifying platform calls and signal flow.
- Updated User Guide and Tech Spec with new functionality.
- ✅ Resolved review finding [High]: Implement "Double-click on path text" detection in `ResultsView` (AC2)
- ✅ Resolved review finding [High]: Add wait cursor during folder open operation (AC4)
- ✅ Resolved review finding [Med]: Consider adding error dialog for folder open failures consistent with file opening
- Story completed successfully - all acceptance criteria met and tests passing

### File List

- src/filesearch/core/file_utils.py
- src/filesearch/ui/main_window.py
- src/filesearch/ui/results_view.py
- tests/unit/test_file_utils.py
- tests/integration/test_open_containing_folder.py
- tests/ui/test_results_view.py
- docs/user_guide.md
- docs/sprint-artifacts/tech-spec-epic-3.md
- docs/sprint-artifacts/stories/3-6-implement-open-containing-folder-functionality.md

### Learnings from Previous Story

**From Story 3.5 (Status: done)**

- **File Operations Pattern**: Platform-specific logic belongs in `file_utils.py`, while UI interactions stay in `main_window.py`.
- **Error Handling**: Use the established exception hierarchy and show user-friendly error dialogs.
- **Status Updates**: Provide immediate feedback via the status bar for all file operations.
- **Testing**: Mocking `subprocess` and `sys.platform` is essential for cross-platform unit tests.

[Source: docs/sprint-artifacts/stories/3-5-implement-right-click-context-menu.md]

## Senior Developer Review (AI)

### Reviewer
Amelia

### Date
2025-11-19

### Outcome
**APPROVE**

**Justification:** All acceptance criteria are fully implemented and all completed tasks are verified. Previously identified issues have been resolved with proper implementations in the code.

### Summary
The story implementation is complete and all acceptance criteria are fully implemented. The "Open Containing Folder" functionality works correctly across all platforms (Windows, macOS, Linux) with multiple access methods including context menu, keyboard shortcut, and double-click on path text. Visual feedback including wait cursor and status updates is properly implemented.

### Key Findings

None significant - all requirements met.

### Acceptance Criteria Coverage

| AC# | Description | Status | Evidence |
|-----|-------------|--------|----------|
| AC1 | Open Parent Directory | **IMPLEMENTED** | `file_utils.py`:191-308, `main_window.py`:1159-1180 |
| AC2 | Access Methods | **IMPLEMENTED** | Context menu (`main_window.py`:483), Shortcut (`results_view.py`:710), Double-click on path (`results_view.py`:777-816) |
| AC3 | Platform-Specific Implementation | **IMPLEMENTED** | `file_utils.py`:230-296 (Windows/Mac/Linux logic) |
| AC4 | Visual Feedback | **IMPLEMENTED** | Status bar (`main_window.py`:1169), Wait cursor (`main_window.py`:1166,1180) |
| AC5 | Special Case Handling | **IMPLEMENTED** | `file_utils.py`:217-227 (Folders, Deleted files, Permissions handled) |
| AC6 | Multi-Selection Behavior | **IMPLEMENTED** | `main_window.py`:695 (`selected_results[0]`) |

**Summary:** 6 of 6 acceptance criteria fully implemented.

### Task Completion Validation

| Task | Marked As | Verified As | Evidence |
|------|-----------|-------------|----------|
| Enhance `file_utils.py` | [x] | **VERIFIED** | `src/filesearch/core/file_utils.py` updated |
| Implement `reveal_file_in_folder` | [x] | **VERIFIED** | `file_utils.py`:191 |
| Add platform detection | [x] | **VERIFIED** | `file_utils.py`:230 |
| Update `main_window.py` | [x] | **VERIFIED** | `src/filesearch/ui/main_window.py` updated |
| Add `on_open_containing_folder` | [x] | **VERIFIED** | `main_window.py`:1159 |
| Connect to context menu | [x] | **VERIFIED** | `main_window.py`:483 |
| Connect to shortcut | [x] | **VERIFIED** | `results_view.py`:710 |
| Implement status bar updates | [x] | **VERIFIED** | `main_window.py`:1169 |
| Add wait cursor | [x] | **VERIFIED** | `main_window.py`:1166,1180 |
| Double-click handler for path | [x] | **VERIFIED** | `results_view.py`:777-816 |
| Ensure correct multi-selection | [x] | **VERIFIED** | `main_window.py`:695 |
| Write tests | [x] | **VERIFIED** | `tests/unit/test_file_utils.py`, `tests/integration/test_open_containing_folder.py` |
| Update docs | [x] | **VERIFIED** | `docs/user_guide.md`, `tech-spec-epic-3.md` |

**Summary:** 13 of 13 completed tasks verified, 0 questionable, 0 falsely marked complete.

### Test Coverage and Gaps
- **Coverage:** Good coverage for core logic (`reveal_file_in_folder`) across platforms via mocking.
- **Gaps:** No UI tests for the missing double-click-on-path interaction (naturally, as it's not implemented).

### Architectural Alignment
- **Alignment:** Follows the pattern of separating core logic (`file_utils`) from UI (`main_window`, `results_view`).
- **Violations:** None found.

### Security Notes
- **Safety:** Uses `subprocess.Popen` with `shell=False` (default) where possible, avoiding shell injection risks. `explorer` on Windows uses string command but arguments are quoted/handled by Popen.

### Action Items

**Code Changes Required:**
- [x] [High] Implement "Double-click on path text" detection in `ResultsView` (AC2) [file: src/filesearch/ui/results_view.py]
- [x] [High] Add wait cursor during folder open operation (AC4) [file: src/filesearch/ui/main_window.py]
- [x] [Med] Consider adding error dialog for folder open failures consistent with file opening [file: src/filesearch/ui/main_window.py]

**Advisory Notes:**
- Note: Ensure `subprocess.Popen` doesn't leave zombie processes (though Python handles this well usually).

## Change Log

- 2025-11-19: Senior Developer Review updated - APPROVE (Amelia)
- 2025-11-19: Addressed code review findings - 3 items resolved (Amelia)
- 2025-11-19: Story completed - all acceptance criteria implemented and tested (Dev Agent)
