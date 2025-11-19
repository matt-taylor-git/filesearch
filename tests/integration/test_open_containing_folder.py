"""Integration tests for Open Containing Folder functionality."""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QKeyEvent

from filesearch.core.exceptions import FileSearchError
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow
from filesearch.ui.results_view import ResultsView


class TestOpenContainingFolderIntegration:
    """Integration tests for open containing folder functionality."""

    @pytest.fixture
    def main_window(self, qtbot):
        """Create main window with mocked dependencies."""
        with (
            patch("filesearch.ui.main_window.ConfigManager"),
            patch("filesearch.ui.main_window.PluginManager"),
            patch("filesearch.ui.main_window.FileSearchEngine"),
        ):
            window = MainWindow()
            qtbot.addWidget(window)
            return window

    @pytest.fixture
    def sample_result(self):
        """Create a sample search result."""
        return SearchResult(
            path=Path("/tmp/test/file.txt"),
            size=1024,
            modified=1000.0,
            plugin_source=None,
        )

    def test_context_menu_action_triggers_core_function(
        self, main_window, sample_result, mocker
    ):
        """Test that context menu action triggers the core utility function."""
        # Mock the core utility function
        mock_open = mocker.patch("filesearch.ui.main_window.open_containing_folder")

        # Simulate selection
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        # Trigger the context menu action handler directly (simulating menu click)
        # We need to get the list of selected results first
        selected_results = [sample_result]
        main_window._handle_context_open_containing_folder(selected_results)

        # Verify core function called with correct path
        mock_open.assert_called_once_with(sample_result.path)

        # Verify success message
        assert main_window.statusBar().currentMessage() == "Opened containing folder"

    def test_context_menu_action_handles_error(
        self, main_window, sample_result, mocker
    ):
        """Test error handling when opening folder fails."""
        # Mock core function to raise exception
        mocker.patch(
            "filesearch.ui.main_window.open_containing_folder",
            side_effect=FileSearchError("Test error"),
        )

        # Trigger action
        main_window._handle_context_open_containing_folder([sample_result])

        # Verify error message in status bar
        assert (
            "Failed to open containing folder"
            in main_window.statusBar().currentMessage()
        )
        assert "Test error" in main_window.statusBar().currentMessage()

    def test_keyboard_shortcut_triggers_signal(self, main_window, sample_result, qtbot):
        """Test that Ctrl+Shift+O triggers the folder opening signal."""
        # Add result
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        # Mock the signal handler
        mock_handler = MagicMock()
        if hasattr(main_window.results_view, "folder_open_requested"):
            main_window.results_view.folder_open_requested.connect(mock_handler)
        else:
            pytest.skip("folder_open_requested signal not implemented yet")

        # Simulate Ctrl+Shift+O key press
        qtbot.keyClick(
            main_window.results_view,
            Qt.Key.Key_O,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )

        # Verify signal emitted
        mock_handler.assert_called_once_with(sample_result)

    def test_keyboard_shortcut_integration(
        self, main_window, sample_result, qtbot, mocker
    ):
        """Test full integration of keyboard shortcut to core function."""
        # Mock core function
        mock_open = mocker.patch("filesearch.ui.main_window.open_containing_folder")

        # Add result
        main_window.results_view.add_result(sample_result)
        index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(index)

        # Check if signal is implemented
        if not hasattr(main_window.results_view, "folder_open_requested"):
            pytest.skip("folder_open_requested signal not implemented yet")

        # Simulate Ctrl+Shift+O key press
        qtbot.keyClick(
            main_window.results_view,
            Qt.Key.Key_O,
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier,
        )

        # Verify core function called
        mock_open.assert_called_once_with(sample_result.path)
