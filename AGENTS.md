# AGENTS.md

Guidance for coding agents and contributors working in this repository.

## Project summary

File Search is a Python 3.9+ desktop application built with PyQt6. It provides fast recursive filename search, a three-panel UI, sidebar-based scope selection, result sorting, details/context actions, and a plugin architecture.

## Runbook

```bash
# Run the app
python -m filesearch
python -m filesearch --debug

# Tests
python -m pytest
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m ui

# Formatting / linting
black src/ tests/
flake8 src/ tests/
pre-commit run --all-files
```

If the local shell has no `python` shim, use the project virtualenv directly, for example `venv/bin/python -m filesearch --debug` or `venv/bin/python -m pytest ...`.

For PyQt tests in headless automation, prefer:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/unit/test_main_window.py
```

## Repository map

```text
src/filesearch/main.py                 Application entrypoint and CLI parsing
src/filesearch/core/                   Search engine, config, security, sorting, file helpers
src/filesearch/models/                 Search result data structures
src/filesearch/plugins/                Plugin interfaces and loading
src/filesearch/ui/main_window.py       Main three-panel window
src/filesearch/ui/sidebar_widget.py    Sidebar locations, chips, tags, storage
src/filesearch/ui/results_view.py      Search results list
src/filesearch/ui/details_panel.py     Selected-file details and actions
src/filesearch/ui/search_controls/     Search bar, hidden directory control, progress, status
src/filesearch/ui/settings/            Settings dialog tabs
src/filesearch/ui/theme.py             Centralized colors, spacing, fonts, and QSS
tests/unit/                            Unit tests
tests/integration/                     Integration tests
tests/ui/                              UI tests with pytest-qt
```

## Working conventions

- Use `pathlib.Path` for paths.
- Use `loguru` for logging; do not add `print()` debugging.
- Keep business logic in `core/`; avoid UI imports there.
- Keep UI responsive. Long-running work belongs in workers/threads and should communicate via Qt signals.
- Search cancellation/restart is managed by `MainWindow`: keep one active filesystem worker at a time, queue only the latest restart request, and ignore stale progress/results after cancellation.
- Keep visual styling centralized in `src/filesearch/ui/theme.py`.
- Do not introduce widget-level inline `setStyleSheet()` calls when a theme/QSS update will do.
- Preserve the sidebar-first search-scope UX. The hidden `DirectorySelectorWidget` exists as shared state plumbing, not as the primary visible control.
- Keep docs aligned with actual behavior, especially CLI options, config format, and repository URLs.

## Testing expectations

- Prefer focused tests when changing a small area.
- Add or update unit tests when changing sidebar behavior, search controls, or config-driven startup behavior.
- UI tests rely on `pytest-qt`; environment-specific temp-directory permission issues can affect local runs, so prefer `python -m pytest` and isolate failures carefully.
- On macOS/headless runs, use `QT_QPA_PLATFORM=offscreen` to avoid Cocoa initialization failures.
- Be careful with tests that can open modal dialogs or trigger real searches via auto-search debounce; isolate them and clean up any hung pytest process before continuing.

## Documentation to keep in sync

- `README.md` for installation, usage, CLI options, and contributor commands
- `docs/user_guide.md` for end-user workflows
- `docs/configuration.md` for config behavior
- `docs/plugin-development.md` for plugin changes
