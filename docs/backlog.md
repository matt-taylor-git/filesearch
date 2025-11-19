# Engineering Backlog

This backlog collects cross-cutting or future action items that emerge from reviews and planning.

Routing guidance:

- Use this file for non-urgent optimizations, refactors, or follow-ups that span multiple stories/epics.
- Must-fix items to ship a story belong in that story's `Tasks / Subtasks`.
- Same-epic improvements may also be captured under the epic Tech Spec `Post-Review Follow-ups` section.

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
| ---- | ----- | ---- | ---- | -------- | ----- | ------ | ----- |
| 2025-11-17 | 3.1 | 3 | Bug | High | TBD | Open | CRITICAL: Complete start_search method - Create SearchWorker and connect signals [file: src/filesearch/ui/main_window.py:324-358] |
| 2025-11-17 | 3.1 | 3 | Enhancement | High | TBD | Open | Implement virtual scrolling in ResultsModel for performance requirements [file: src/filesearch/ui/results_view.py:11-50] |
| 2025-11-17 | 3.1 | 3 | Enhancement | High | TBD | Open | Add keyboard navigation (Up/Down, Page Up/Down, Home/End) to ResultsView [file: src/filesearch/ui/results_view.py:185-265] |
| 2025-11-17 | 3.1 | 3 | Enhancement | Med | TBD | Open | Configure ResultsView to occupy bottom 70% of MainWindow layout [file: src/filesearch/ui/main_window.py:232-234] |
| 2025-11-17 | 3.1 | 3 | Enhancement | Med | TBD | Open | Add auto-scroll to first result when search completes [file: src/filesearch/ui/results_view.py:245-254] |
| 2025-11-15 | 2.6 | 2 | Bug | High | TBD | Open | Add QApplication import to search_controls.py to fix runtime crashes [file: src/filesearch/ui/search_controls.py:16-35] |
| 2025-11-15 | 2.6 | 2 | Enhancement | Med | TBD | Open | Add audio_notification_on_search_complete to ConfigManager defaults [file: src/filesearch/core/config_manager.py:61-83] |
| 2025-11-14 | 1.4 | 1 | Enhancement | High | TBD | Open | Implement entry point plugin discovery (AC1) [file: src/filesearch/plugins/plugin_manager.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | High | TBD | Open | Load plugin metadata from plugin.json files (AC1) [file: src/filesearch/plugins/plugin_base.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Add plugin dependency resolution support [file: src/filesearch/plugins/plugin_manager.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Add plugin API versioning support [file: src/filesearch/plugins/plugin_base.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Update search_engine.py to support plugin search results [file: src/filesearch/core/search_engine.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Implement plugin source indicators in results [file: src/filesearch/ui/main_window.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Enhance plugin configuration dialogs [file: src/filesearch/ui/settings_dialog.py] |
| 2025-11-14 | 1.4 | 1 | Enhancement | Low | TBD | Open | Create plugin development documentation [file: docs/plugin-development.md] |
| 2025-11-14 | 1.4 | 1 | Bug | High | TBD | Open | Fix test failures preventing 100% pass rate (plugin name initialization, search result format, signal connections, plugin discovery) |
| 2025-11-14 | 1.4 | 1 | Enhancement | High | TBD | Open | Implement plugin source indicators in results display UI |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Enhance plugin configuration dialogs with proper form-based UI |
| 2025-11-14 | 1.4 | 1 | Enhancement | Med | TBD | Open | Implement plugin result highlighting in search results |
| 2025-11-14 | 1.4 | 1 | Bug | Low | TBD | Open | Fix test fixture issues (temp_dir availability) |
| | 2025-11-15 | 2.3 | 2 | Enhancement | Medium | TBD | Open | Implement auto-complete for common paths (home, documents, desktop) in addition to recent directories (AC #2.3) [file: src/filesearch/ui/search_controls.py:224-236] |
| | 2025-11-15 | 2.3 | 2 | Enhancement | Medium | TBD | Open | Verify and enhance right-click dropdown behavior to match left-click dropdown functionality (AC #4.2) [file: src/filesearch/ui/search_controls.py:585-601] |
| | 2025-11-15 | 2.3 | 2 | Enhancement | Medium | TBD | Open | Add explicit network path testing and documentation to validate cross-platform network path support (AC #6.3) [file: src/filesearch/core/file_utils.py:274-294] |
| | 2025-11-15 | 2.3 | 2 | Enhancement | Medium | TBD | Open | Add auto-complete for common paths (home, documents, desktop) to complement recent directories (AC #2.3) [file: src/filesearch/ui/search_controls.py:705-728] |
| | 2025-11-17 | 3.1 | 3 | Bug | High | TBD | Open | Implement virtual scrolling in QListView to render only visible items (AC #1, AC #5) [file: src/filesearch/ui/results_view.py:143-213] |
| | 2025-11-17 | 3.1 | 3 | Bug | High | TBD | Open | Connect ResultsView.add_result to SearchEngine.result_found signal for real-time updates (AC "real-time updates") [file: src/filesearch/ui/main_window.py:255-275] |
| | 2025-11-17 | 3.1 | 3 | Bug | High | TBD | Open | Implement keyboard navigation (Up/Down, Page Up/Down, Home/End) in ResultsView (AC #3) [file: src/filesearch/ui/results_view.py:143-213] |
| | 2025-11-17 | 3.1 | 3 | Enhancement | High | TBD | Open | Add lazy loading for file metadata when items become visible (AC #5) [file: src/filesearch/ui/results_view.py:143-213] |
| | 2025-11-17 | 3.1 | 3 | Enhancement | High | TBD | Open | Implement icon caching by extension to minimize disk I/O (AC #5) [file: src/filesearch/ui/results_view.py:22-48] |
| | 2025-11-17 | 3.1 | 3 | Enhancement | Medium | TBD | Open | Configure ResultsView to occupy bottom 70% of MainWindow (AC #1) [file: src/filesearch/ui/main_window.py:200-240] |
| | 2025-11-17 | 3.1 | 3 | Bug | Medium | TBD | Open | Fix file size formatting to use binary prefixes (KiB, MiB, GiB) instead of decimal (AC #2) [file: src/filesearch/models/search_result.py:26-36] |
| | 2025-11-17 | 3.1 | 3 | Enhancement | Medium | TBD | Open | Add "Searching..." empty state during search operations (AC #4) [file: src/filesearch/ui/results_view.py:169-174] |
| 2025-11-19 | 3.6 | 3 | Enhancement | High | TBD | Open | Implement "Double-click on path text" detection in ResultsView (AC2) [file: src/filesearch/ui/results_view.py] |
| 2025-11-19 | 3.6 | 3 | Enhancement | High | TBD | Open | Add wait cursor during folder open operation (AC4) [file: src/filesearch/ui/main_window.py] |
| 2025-11-19 | 3.6 | 3 | Enhancement | Med | TBD | Open | Consider adding error dialog for folder open failures consistent with file opening [file: src/filesearch/ui/main_window.py] |
