"""Integration tests for Open Containing Folder functionality."""

from pathlib import Path
from typing import Any

import pytest
from PyQt6.QtCore import Qt

from filesearch.core.exceptions import FileSearchError
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


class TestOpenContainingFolderIntegration:
    """Integration tests for open containing folder functionality."""

    @pytest.fixture
    def main_window(self, qtbot: Any, application_runtime: Any) -> MainWindow:
        """Create a main window through the hermetic runtime boundary."""
        window = MainWindow(runtime=application_runtime)
        qtbot.addWidget(window)
        return window

    @pytest.fixture
    def sample_result(self, tmp_path: Path) -> SearchResult:
        """Create a sample search result."""
        file_path = tmp_path / "test" / "file.txt"
        file_path.parent.mkdir()
        file_path.write_text("content", encoding="utf-8")
        return SearchResult(
            path=file_path,
            size=file_path.stat().st_size,
            modified=file_path.stat().st_mtime,
            plugin_source=None,
        )

    def test_context_menu_action_triggers_core_function(
        self,
        main_window: MainWindow,
        sample_result: SearchResult,
        desktop_effects: Any,
    ) -> None:
        """Test that context menu action triggers the core utility function."""
        # Simulate selection
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        # Trigger the context menu action handler directly (simulating menu click)
        # We need to get the list of selected results first
        selected_results = [sample_result]
        main_window._handle_context_open_containing_folder(selected_results)

        # Verify core function called with correct path
        assert desktop_effects.revealed_files == [sample_result.path]

        # Verify success message
        assert main_window.statusBar().currentMessage() == "Opened containing folder"

    def test_context_menu_action_handles_error(
        self,
        main_window: MainWindow,
        sample_result: SearchResult,
        desktop_effects: Any,
    ) -> None:
        """Test error handling when opening folder fails."""
        desktop_effects.reveal_file_failure = FileSearchError("Test error")

        # Trigger action
        main_window._handle_context_open_containing_folder([sample_result])

        # Verify error message in status bar
        assert (
            "Failed to open containing folder"
            in main_window.statusBar().currentMessage()
        )
        assert "Test error" in main_window.statusBar().currentMessage()

    def test_keyboard_shortcut_triggers_signal(
        self, main_window: MainWindow, sample_result: SearchResult, qtbot: Any
    ) -> None:
        """Test that Ctrl+Shift+O triggers the folder opening signal."""
        # Add result
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        with qtbot.waitSignal(
            main_window.results_view.folder_open_requested, timeout=1000
        ) as signal:
            qtbot.keyClick(
                main_window.results_view,
                Qt.Key.Key_O,
                Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
            )

        assert signal.args == [sample_result]

    def test_keyboard_shortcut_integration(
        self,
        main_window: MainWindow,
        sample_result: SearchResult,
        qtbot: Any,
        desktop_effects: Any,
    ) -> None:
        """Test full integration of keyboard shortcut to core function."""
        # Add result
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        # Simulate Ctrl+Shift+O key press
        qtbot.keyClick(
            main_window.results_view,
            Qt.Key.Key_O,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )

        # Verify core function called
        assert desktop_effects.revealed_files == [sample_result.path]
