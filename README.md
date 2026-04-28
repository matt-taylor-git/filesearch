# File Search

File Search is a desktop file-finding app built with Python and PyQt6. It combines a fast local search engine with a polished three-panel UI, sidebar-driven search scope selection, file-type filters, sorting, details, and an extensible plugin system.

## Features

- Fast recursive filename search with background workers
- Restartable searches: clearing the query cancels the active scan, and changing location or starting a new query restarts cleanly
- Sidebar locations for `Home`, `Documents`, `Desktop`, `Downloads`, `Pictures`, and `Videos`
- Sidebar `Choose Folder...` action for searching any custom directory
- Search history, recent custom folders, and remembered default search location
- File type chips, recent-search tags, and sortable result lists
- Storage tab with a drive summary and treemap drill-down for the active folder
- Details panel and context actions such as open, open containing folder, copy path, rename, and delete
- Configurable settings for search behavior, highlighting, performance, and plugins
- Cross-platform file opening helpers and executable-file safety warnings

## Requirements

- Python 3.9+
- Git

## Installation

### Runtime setup

```bash
git clone https://github.com/matt-taylor-git/filesearch.git
cd filesearch

# Windows
python -m venv venv
venv\Scripts\activate

# macOS / Linux
python3 -m venv venv
source venv/bin/activate

pip install -r requirements.txt
pip install -e .
```

### Development setup

```bash
pip install -r requirements-dev.txt
pre-commit install
```

## Running the app

```bash
# From source
python -m filesearch

# If installed as a script entrypoint
filesearch
```

The app now ships with a bundled application icon in `src/filesearch/resources/icons/`.

### Command-line options

```text
--help, -h     Show help
--version, -v  Show version information
--debug        Enable debug logging
--info         Enable info logging
--warning      Enable warning-only logging
--error        Enable error-only logging
```

## How to use

1. Pick a search location from the left sidebar, or use `Choose Folder...` to browse for any folder.
2. Enter a filename pattern such as `*.py`, `report*`, or `invoice?.pdf`.
3. Press `Enter` in the search box to start the search.
4. Narrow visible results with the sidebar file-type chips.
5. Sort the results list and inspect the selected file in the details panel.
6. Open the `Storage` tab to visualize used space for the currently selected folder.

If a search is already running, changing the query or selected location requests cancellation of the active scan. The app then starts the latest valid query/location automatically once the previous worker stops. Clearing the search box cancels the current scan without starting another one.

## Configuration

The app stores configuration as JSON using `platformdirs`. Settings include:

- default search directory
- case sensitivity
- hidden-file behavior
- result limits
- excluded file extensions
- highlight settings
- plugin settings

The main config file is created automatically in the user's platform-specific config directory as `config.json`.

## Development

### Useful commands

```bash
python -m pytest
python -m pytest -m unit
python -m pytest -m integration
python -m pytest -m ui

black src/ tests/
flake8 src/ tests/
pre-commit run --all-files
```

For PyQt tests in headless or automation contexts, run with Qt's offscreen platform:

```bash
QT_QPA_PLATFORM=offscreen python -m pytest tests/unit/test_main_window.py
```

Some local macOS shells may not expose a `python` shim even when a virtualenv exists; using `venv/bin/python -m pytest ...` is equivalent.

### Release packaging

Standalone desktop bundles are produced with PyInstaller for Windows, macOS, and Linux.

```bash
pip install -e .[release]
python scripts/build_release.py
```

The script creates:

- `dist/FileSearch-windows.zip`
- `dist/FileSearch-macos.zip`
- `dist/FileSearch-linux.tar.gz`

Depending on the OS you run it on, it builds the native artifact for that platform only.

### GitHub Releases

Pushing a version tag such as `v0.1.0` triggers `.github/workflows/release.yml`, which:

- validates the tag matches `filesearch.__version__`
- builds native standalone bundles on Windows, macOS, and Linux
- uploads the packaged artifacts to the matching GitHub Release

The first packaged releases are unsigned, so Windows SmartScreen and macOS Gatekeeper may display warnings until code signing is added.

### Project layout

```text
src/filesearch/
  core/      Search engine, config, security, sorting, filesystem helpers
  models/    Data objects such as SearchResult
  plugins/   Plugin interfaces and built-in plugins
  ui/        Main window, sidebar, results, settings, theme, and search controls
  utils/     Shared helpers such as text highlighting

tests/
  unit/
  integration/
  ui/
```

## Documentation

- [User guide](docs/user_guide.md)
- [Architecture overview](docs/architecture.md)
- [Configuration notes](docs/configuration.md)
- [Plugin development](docs/plugin-development.md)

## Repository

- Repository: https://github.com/matt-taylor-git/filesearch
- Issues: https://github.com/matt-taylor-git/filesearch/issues
