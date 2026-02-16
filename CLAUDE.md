# CLAUDE.md

Cross-platform desktop file search app built with Python 3.9+ and PyQt6. Multi-threaded search engine with plugin architecture.

## Commands

```bash
python -m filesearch              # Run app
python -m filesearch --debug      # Run with debug logging
pytest                            # Run all tests
pytest -m unit                    # Unit tests only
pytest -m integration             # Integration tests
pytest -m ui                      # UI tests (pytest-qt)
pytest --cov=filesearch           # With coverage
black src/ tests/                 # Format
flake8 src/ tests/                # Lint
isort --profile=black src/ tests/ # Sort imports
pre-commit run --all-files        # All checks
```

## Project Structure

```
src/filesearch/
├── main.py                  # Entry point
├── core/
│   ├── search_engine.py     # Multi-threaded search (ThreadPoolExecutor + signals)
│   ├── sort_engine.py       # Result sorting
│   ├── config_manager.py    # JSON config via platformdirs (singleton)
│   ├── config_schema.py     # Config schema/defaults
│   ├── security_manager.py  # Security and permissions
│   ├── file_utils.py        # File operations
│   └── exceptions.py        # Exception hierarchy
├── ui/
│   ├── main_window.py       # Main GUI window
│   ├── results_view.py      # Search results display
│   ├── settings_dialog.py   # Settings dialog
│   ├── sort_controls.py     # Sort UI controls
│   └── theme.py             # Centralized theme system
├── plugins/
│   ├── plugin_base.py       # Abstract SearchPlugin base class
│   ├── plugin_manager.py    # Plugin lifecycle management
│   └── builtin/example_plugin.py
├── models/
│   └── search_result.py     # SearchResult dataclass
└── utils/
    └── highlight_engine.py  # Text highlighting
```

Tests mirror this in `tests/{unit,integration,ui}/`.

## Key Conventions

### Architecture Rules
- **core/**: Business logic only, no UI imports
- **ui/**: PyQt6 GUI components, never block the UI thread (use QThread + signals)
- **models/**: Dataclasses for data structures
- **plugins/**: Extension point via `SearchPlugin` base class
- Search runs in worker threads, results stream via PyQt signals/slots

### Code Style
- **Formatter**: Black (88 char line length)
- **Linting**: flake8 (ignores E203, F401 in `__init__.py`)
- **Imports**: isort with `--profile=black`
- **Paths**: Always `pathlib.Path`, never `os.path`
- **Logging**: `loguru` (`from loguru import logger`), never `print()`
- **Type hints**: Required on all function signatures
- **Commits**: Conventional format — `feat(scope): message`, `fix(scope): message`, etc.

### Exception Hierarchy (`core/exceptions.py`)
- `FileSearchError` (base) → `SearchError`, `PluginError`, `ConfigError`, `UIError`
- Always raise with context: `raise SearchError("msg", path=str(p), cause=e)`

### Theme System (`ui/theme.py`) — IMPORTANT
- All styling lives in `theme.py`: `Colors`, `Fonts`, `Spacing` classes + `APP_STYLESHEET`
- `apply_theme(app)` is called at startup in `main.py`
- Style widgets via `setProperty("class", "variant-name")` + QSS selectors
- **NEVER** use inline `setStyleSheet()` on individual widgets
- To add new styled widgets: add QSS to `APP_STYLESHEET`, use `setProperty`/`setObjectName` in code

### Testing
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.ui`
- UI tests use `pytest-qt` fixtures (`qtbot`)
- Coverage target: >80% overall, >90% core

## Additional Docs
- `docs/PRD.md` — Product requirements
- `docs/architecture.md` — Architecture decisions
- `docs/epics.md` — Feature breakdown
- `docs/plugin-development.md` — Plugin dev guide
- `docs/configuration.md` — Config options
