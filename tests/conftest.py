"""Hermetic application composition shared by unit, integration, and UI tests."""

from __future__ import annotations

import os
from collections.abc import Sequence
from pathlib import Path
from typing import Any

import pytest
from loguru import logger

from filesearch.core.application_runtime import ApplicationRuntime

# This must be set before test modules import PyQt.
os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
MINIMUM_STATEMENT_COVERAGE = 80.0


@pytest.hookimpl(wrapper=True, tryfirst=True)
def pytest_runtestloop(session: pytest.Session):
    """Enforce statement coverage separately from reported branch coverage."""
    result = yield
    if session.config.option.collectonly or session.config.option.no_cov:
        return result

    cov_plugin = session.config.pluginmanager.getplugin("_cov")
    if cov_plugin is None or cov_plugin.cov_controller is None:
        return result

    coverage = cov_plugin.cov_controller.cov
    measured_files = coverage.get_data().measured_files()
    statement_count = 0
    missing_count = 0
    for filename in measured_files:
        _path, statements, _excluded, missing, _formatted = coverage.analysis2(filename)
        statement_count += len(statements)
        missing_count += len(missing)

    covered_count = statement_count - missing_count
    percent = 100 * covered_count / statement_count if statement_count else 100.0
    reporter = session.config.pluginmanager.getplugin("terminalreporter")
    reporter.write_sep("=", "statement coverage gate")
    reporter.write(
        f"Production statement coverage: {percent:.2f}% "
        f"({covered_count}/{statement_count}); "
        f"required: {MINIMUM_STATEMENT_COVERAGE:.2f}%\n",
        **(
            {"red": True, "bold": True}
            if percent < MINIMUM_STATEMENT_COVERAGE
            else {"green": True}
        ),
    )
    if percent < MINIMUM_STATEMENT_COVERAGE:
        session.testsfailed += 1


def pytest_collection_modifyitems(items: list[pytest.Item]) -> None:
    """Classify tests by their top-level suite directory."""
    suite_markers = {"unit", "integration", "ui"}
    for item in items:
        relative_path = Path(str(item.path)).relative_to(Path(__file__).parent)
        if relative_path.parts and relative_path.parts[0] in suite_markers:
            item.add_marker(getattr(pytest.mark, relative_path.parts[0]))


class RecordingDesktopEffects:
    """Desktop adapter that records effects instead of contacting the desktop."""

    def __init__(self) -> None:
        self.open_file_failure: Exception | None = None
        self.reveal_file_failure: Exception | None = None
        self.copy_text_failure: Exception | None = None
        self.copy_files_failure: Exception | None = None
        self.show_properties_failure: Exception | None = None
        self.opened_files: list[Path] = []
        self.revealed_files: list[Path] = []
        self.opened_with: list[tuple[Path, dict[str, Any]]] = []
        self.copied_text: list[str] = []
        self.copied_files: list[list[Path]] = []
        self.errors: list[tuple[str, str]] = []
        self.warnings: list[tuple[str, str]] = []
        self.information: list[tuple[str, str]] = []
        self.properties: list[Path] = []
        self.directory_choice: Path | None = None
        self.directory_requests: list[tuple[Path, str]] = []
        self.application_choice: Path | None = None
        self.confirmed = False
        self.executable_response = (False, False)
        self.executable_prompts: list[str] = []
        self.color_choice: str | None = None
        self.beep_count = 0

    def _raise_failure(self, failure: Exception | None) -> None:
        if failure is not None:
            raise failure

    def open_file(self, path: Path) -> None:
        self._raise_failure(self.open_file_failure)
        self.opened_files.append(path)

    def reveal_file(self, path: Path) -> None:
        self._raise_failure(self.reveal_file_failure)
        self.revealed_files.append(path)

    def open_with(self, path: Path, application: dict[str, Any]) -> None:
        self.opened_with.append((path, application))

    def choose_directory(
        self, parent: Any, initial: Path, *, title: str = "Select Search Directory"
    ) -> Path | None:
        self.directory_requests.append((initial, title))
        return self.directory_choice

    def choose_application(self, parent: Any) -> Path | None:
        return self.application_choice

    def copy_text(self, text: str) -> None:
        self._raise_failure(self.copy_text_failure)
        self.copied_text.append(text)

    def copy_files(self, paths: Sequence[Path]) -> None:
        self._raise_failure(self.copy_files_failure)
        self.copied_files.append(list(paths))

    def confirm(
        self, parent: Any, title: str, message: str, *, default_yes: bool = False
    ) -> bool:
        return self.confirmed

    def show_error(self, parent: Any, title: str, message: str) -> None:
        self.errors.append((title, message))

    def show_warning(self, parent: Any, title: str, message: str) -> None:
        self.warnings.append((title, message))

    def show_info(self, parent: Any, title: str, message: str) -> None:
        self.information.append((title, message))

    def choose_color(self, parent: Any, initial: str, title: str) -> str | None:
        return self.color_choice

    def beep(self) -> None:
        self.beep_count += 1

    def show_properties(self, parent: Any, path: Path) -> None:
        self._raise_failure(self.show_properties_failure)
        self.properties.append(path)

    def confirm_executable(self, parent: Any, message: str) -> tuple[bool, bool]:
        self.executable_prompts.append(message)
        return self.executable_response


@pytest.fixture(autouse=True)
def hermetic_user_environment(tmp_path_factory, monkeypatch):
    """Redirect conventional user directories to per-test temporary state."""
    state_dir = tmp_path_factory.mktemp("hermetic-user")
    home_dir = state_dir / "home"
    home_dir.mkdir()
    for variable, value in {
        "HOME": home_dir,
        "USERPROFILE": home_dir,
        "XDG_CONFIG_HOME": state_dir / "xdg-config",
        "XDG_DATA_HOME": state_dir / "xdg-data",
        "XDG_CACHE_HOME": state_dir / "xdg-cache",
    }.items():
        monkeypatch.setenv(variable, str(value))
    logger.disable("filesearch")
    yield
    logger.enable("filesearch")


@pytest.fixture
def desktop_effects() -> RecordingDesktopEffects:
    """Return a fresh recording desktop adapter."""
    return RecordingDesktopEffects()


@pytest.fixture
def application_runtime(tmp_path_factory, desktop_effects) -> ApplicationRuntime:
    """Compose File Search entirely beneath one test-owned directory."""
    home_dir = Path.home()
    state_dir = tmp_path_factory.mktemp("application-runtime")
    return ApplicationRuntime(
        home_dir=home_dir,
        config_dir=state_dir / "config",
        log_dir=state_dir / "logs",
        desktop_effects=desktop_effects,
    )
