# Engineering Backlog

This backlog collects cross-cutting or future action items that emerge from reviews and planning.

Routing guidance:

- Use this file for non-urgent optimizations, refactors, or follow-ups that span multiple stories/epics.
- Must-fix items to ship a story belong in that story's `Tasks / Subtasks`.
- Same-epic improvements may also be captured under the epic Tech Spec `Post-Review Follow-ups` section.

| Date | Story | Epic | Type | Severity | Owner | Status | Notes |
| ---- | ----- | ---- | ---- | -------- | ----- | ------ | ----- |
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
