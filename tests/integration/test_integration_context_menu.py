"""Integration tests for context-menu workflows through application composition."""

from pathlib import Path
from typing import Any

import pytest

from filesearch.core.exceptions import FileSearchError
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


@pytest.fixture
def search_results(tmp_path: Path) -> list[SearchResult]:
    """Create search results backed by test-owned files."""
    paths = [tmp_path / "file1.txt", tmp_path / "file2.py"]
    for index, path in enumerate(paths, start=1):
        path.write_text(f"content{index}", encoding="utf-8")

    return [
        SearchResult(
            path=path,
            size=path.stat().st_size,
            modified=path.stat().st_mtime,
        )
        for path in paths
    ]


@pytest.fixture
def main_window(qtbot: Any, application_runtime: Any) -> MainWindow:
    """Create a main window with temporary state and controlled desktop effects."""
    window = MainWindow(runtime=application_runtime)
    qtbot.addWidget(window)
    return window


def test_open_action_records_file_and_recent_history(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """Opening a context-menu result reaches the desktop boundary and history."""
    main_window._handle_context_open([search_results[0]])

    assert desktop_effects.opened_files == [search_results[0].path]
    assert main_window.config_manager.get("recent_files.opened_files") == [
        str(search_results[0].path)
    ]
    assert main_window.statusBar().currentMessage() == "Opened: file1.txt"


def test_copy_path_workflow_supports_multiple_results(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """Copy Path sends newline-delimited paths to the controlled clipboard."""
    main_window._handle_context_copy_path(search_results)

    expected_text = f"{search_results[0].path}\n{search_results[1].path}"
    assert desktop_effects.copied_text == [expected_text]
    assert main_window.statusBar().currentMessage() == "Path copied to clipboard"


def test_delete_cancellation_preserves_file(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """Declining delete leaves the test-owned file untouched."""
    desktop_effects.confirmed = False

    main_window._handle_context_delete([search_results[0]])

    assert search_results[0].path.exists()
    assert main_window.statusBar().currentMessage() == "Delete cancelled"


def test_properties_workflow_uses_desktop_boundary(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """Properties requests are contained by the runtime adapter."""
    main_window._handle_context_properties([search_results[0]])

    assert desktop_effects.properties == [search_results[0].path]


def test_file_opening_failure_is_reported(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """A desktop file-opening failure remains visible to the user."""
    desktop_effects.open_file_failure = FileSearchError("File opening failed")

    main_window._handle_context_open([search_results[0]])

    assert desktop_effects.opened_files == []
    assert main_window.statusBar().currentMessage() == "Failed to open: file1.txt"


def test_clipboard_failure_is_reported(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """A desktop clipboard failure remains visible to the user."""
    desktop_effects.copy_text_failure = RuntimeError("Clipboard unavailable")

    main_window._handle_context_copy_path([search_results[0]])

    assert (
        main_window.statusBar().currentMessage()
        == "Failed to copy path: Clipboard unavailable"
    )


def test_properties_failure_is_reported(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """A properties-dialog failure remains visible to the user."""
    desktop_effects.show_properties_failure = RuntimeError("Dialog creation failed")

    main_window._handle_context_properties([search_results[0]])

    assert (
        main_window.statusBar().currentMessage()
        == "Failed to show properties: Dialog creation failed"
    )


def test_reveal_and_clipboard_file_workflows_use_desktop_boundary(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """Reveal and file-copy effects stay inside the controlled runtime adapter."""
    main_window._handle_context_open_containing_folder([search_results[0]])
    main_window._handle_context_copy_file([search_results[0]])

    assert desktop_effects.revealed_files == [search_results[0].path]
    assert desktop_effects.copied_files == [[search_results[0].path]]
    assert main_window.statusBar().currentMessage() == "File copied to clipboard"


def test_file_clipboard_failure_falls_back_to_copying_path(
    main_window: MainWindow,
    search_results: list[SearchResult],
    desktop_effects: Any,
) -> None:
    """File-copy failure falls back to a controlled plain-text clipboard effect."""
    desktop_effects.copy_files_failure = RuntimeError("MIME unavailable")

    main_window._handle_context_copy_file([search_results[0]])

    assert desktop_effects.copied_files == []
    assert desktop_effects.copied_text == [str(search_results[0].path)]
    assert (
        main_window.statusBar().currentMessage()
        == "Failed to copy file object, copied path instead"
    )
