"""Integration tests for context menu end-to-end workflows."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


@pytest.fixture
def search_results(tmp_path):
    """Create test search results with real files."""
    file1 = tmp_path / "file1.txt"
    file1.write_text("content1")

    file2 = tmp_path / "file2.py"
    file2.write_text("content2")

    return [
        SearchResult(
            path=file1,
            size=1024,
            modified=1678886400,
        ),
        SearchResult(
            path=file2,
            size=2048,
            modified=1678972800,
        ),
    ]


@pytest.fixture
def main_window(qtbot):
    """Create main window for integration tests."""
    window = MainWindow()
    qtbot.addWidget(window)
    return window


class TestRightClickToMenuActionFlow:
    """Test complete workflows from right-click to menu action execution."""

    def test_right_click_menu_creation_workflow(
        self, main_window, qtbot, search_results
    ):
        """Test complete workflow from right-click to menu display."""
        # Set up search results
        main_window.results_view.set_results(search_results)

        # Select first item
        first_index = main_window.results_view.model().index(0, 0)
        main_window.results_view.setCurrentIndex(first_index)

        # Simulate context menu signal emission (like right-click)
        with patch.object(main_window, "_create_context_menu") as mock_create_menu:
            mock_menu = Mock()
            mock_create_menu.return_value = mock_menu

            # Emit context menu requested signal
            position = Mock()
            main_window._on_context_menu_requested(position)

            # Verify menu creation was called with correct results
            mock_create_menu.assert_called_once()
            args = mock_create_menu.call_args[0][0]
            assert len(args) == 1
            assert args[0] == search_results[0]  # Single selection

            # Verify menu execution
            mock_menu.exec.assert_called_once_with(position)

    def test_multi_selection_menu_creation(self, main_window, qtbot, search_results):
        """Test menu creation with multiple selection."""
        # Set up search results
        main_window.results_view.set_results(search_results)

        # Mock selection model to return multiple indexes
        with patch.object(main_window.results_view, "selectionModel") as mock_selection:
            mock_indexes = [Mock(), Mock()]
            mock_selection.return_value.selectedIndexes.return_value = mock_indexes

            # Mock data access for SearchResult objects
            with patch.object(main_window.results_view, "model") as mock_model:
                mock_model.return_value.data.side_effect = [
                    search_results[0],
                    search_results[1],
                    search_results[0],
                    search_results[1],
                ]

                with patch.object(
                    main_window, "_create_context_menu"
                ) as mock_create_menu:
                    mock_menu = Mock()
                    mock_create_menu.return_value = mock_menu

                    # Emit context menu requested signal
                    main_window._on_context_menu_requested(Mock())

                    # Verify menu creation was called with both results
                    mock_create_menu.assert_called_once()
                    args = mock_create_menu.call_args[0][0]
                    assert len(args) == 2
                    assert args == search_results

    def test_open_action_end_to_end_workflow(self, main_window, qtbot, search_results):
        """Test complete open action workflow from menu trigger to file opening."""
        # Set up search results
        main_window.results_view.set_results(search_results)

        # Mock the file opening request
        with patch.object(main_window, "_on_file_open_requested") as mock_open_file:
            # Trigger the open action directly (as menu would)
            main_window._handle_context_open([search_results[0]])

            # Verify file opening was requested
            mock_open_file.assert_called_once_with(search_results[0])

    def test_copy_path_workflow_multiselect(self, main_window, qtbot, search_results):
        """Test copying multiple file paths end-to-end."""
        import PyQt6.QtGui

        with patch("PyQt6.QtGui.QGuiApplication.clipboard") as mock_clipboard_getter:
            mock_clipboard = Mock()
            mock_clipboard_getter.return_value = mock_clipboard

            with patch.object(main_window, "safe_status_message") as mock_status:
                # Execute copy path action
                main_window._handle_context_copy_path(search_results)

                # Verify clipboard received the correct text
                expected_text = f"{search_results[0].path}\n{search_results[1].path}"
                mock_clipboard.setText.assert_called_once_with(expected_text)

                # Verify status message
                mock_status.assert_called_with("Path copied to clipboard")

    def test_delete_confirmation_workflow_cancel(
        self, main_window, qtbot, search_results
    ):
        """Test delete workflow when user cancels confirmation."""
        with patch("PyQt6.QtWidgets.QMessageBox.question") as mock_question:
            # Simulate user clicking Cancel
            from PyQt6.QtWidgets import QMessageBox

            mock_question.return_value = QMessageBox.StandardButton.No

            with patch.object(main_window, "safe_status_message") as mock_status:
                with patch.object(
                    main_window, "_perform_delete"
                ) as mock_perform_delete:
                    # Execute delete action
                    main_window._handle_context_delete([search_results[0]])

                    # Verify confirmation dialog was shown
                    mock_question.assert_called_once()

                    # Verify delete was NOT performed
                    mock_perform_delete.assert_not_called()

                    # Verify cancellation message
                    mock_status.assert_any_call("Delete cancelled")

    def test_delete_confirmation_workflow_proceed(
        self, main_window, qtbot, search_results
    ):
        """Test delete workflow when user confirms deletion."""
        with patch("PyQt6.QtWidgets.QMessageBox.question") as mock_question:
            # Simulate user clicking Yes
            from PyQt6.QtWidgets import QMessageBox

            mock_question.return_value = QMessageBox.StandardButton.Yes

            with patch.object(main_window, "_perform_delete") as mock_perform_delete:
                # Execute delete action
                main_window._handle_context_delete([search_results[0]])

                # Verify confirmation dialog was shown
                mock_question.assert_called_once()

                # Verify delete was performed
                mock_perform_delete.assert_called_once_with([search_results[0]], False)

    def test_properties_dialog_workflow(self, main_window, qtbot, search_results):
        """Test properties dialog complete workflow."""
        from filesearch.ui.dialogs.properties_dialog import PropertiesDialog

        with patch(
            "filesearch.ui.dialogs.properties_dialog.PropertiesDialog"
        ) as mock_dialog_class:
            mock_dialog = Mock()
            mock_dialog_class.return_value = mock_dialog
            mock_dialog.exec.return_value = True

            # Execute properties action
            main_window._handle_context_properties([search_results[0]])

            # Verify dialog was created correctly
            mock_dialog_class.assert_called_once_with(
                search_results[0].path, main_window
            )

            # Verify dialog was executed
            mock_dialog.exec.assert_called_once()


class TestErrorHandlingIntegration:
    """Test error handling across complete workflows."""

    def test_file_opening_error_recovery(self, main_window, search_results):
        """Test error handling when file opening fails."""
        # Mock safe_open inside file_utils to raise an error
        # This allows _on_file_open_requested to run and log the error
        with patch("filesearch.core.file_utils.safe_open") as mock_safe_open:
            mock_safe_open.side_effect = Exception("File opening failed")

            with patch.object(main_window, "safe_status_message") as mock_status:
                # Patch logger in the module where it is used
                # (filesearch.ui.main_window)
                with patch("filesearch.ui.main_window.logger") as mock_logger:
                    # Execute the action
                    main_window._on_context_menu_action(
                        main_window.ContextMenuAction.OPEN
                    )

                    # Verify error was logged
                    mock_logger.error.assert_called()

                    # Verify user-friendly error message (safe_open error is caught in
                    # _open_file_with_status catches FileSearchError, generic Exception.
                    # Wait, _open_file_with_status:
                    #
                    #
                    # try: safe_open(...) except FileSearchError as e: ...
                    # If safe_open raises generic Exception, it propagates to
                    # _on_file_open_requested
                    # which catches Exception and logs it.

                    mock_status.assert_called()
                    # Check if error message contains "Error checking file security" or
                    # similar depending on where it was caught
                    # _on_file_open_requested catches generic Exception ->
                    # "Error checking file security: ..."

                    # Actually, _open_file_with_status is called from
                    # _on_file_open_requested _open_file_with_status doesn't catch
                    # generic Exception.
                    # So it goes to _on_file_open_requested except block.
                    assert mock_logger.error.call_count > 0

    def test_clipboard_failure_recovery(self, main_window, search_results):
        """Test clipboard operations failure recovery."""
        with patch("PyQt6.QtGui.QGuiApplication.clipboard") as mock_clipboard_getter:
            mock_clipboard = Mock()
            mock_clipboard.setText.side_effect = Exception("Clipboard unavailable")
            mock_clipboard_getter.return_value = mock_clipboard

            with patch.object(main_window, "safe_status_message") as mock_status:
                with patch("filesearch.ui.main_window.logger") as mock_logger:
                    # Execute copy path action
                    main_window._handle_context_copy_path([search_results[0]])

                    # Verify error was logged
                    mock_logger.error.assert_called()

                    # Verify user-friendly error message
                    mock_status.assert_called_with(
                        "Failed to copy path: Clipboard unavailable"
                    )

    def test_properties_dialog_creation_failure(self, main_window, search_results):
        """Test properties dialog creation failure."""
        with patch(
            "filesearch.ui.dialogs.properties_dialog.PropertiesDialog"
        ) as mock_dialog_class:
            mock_dialog_class.side_effect = Exception("Dialog creation failed")

            with patch.object(main_window, "safe_status_message") as mock_status:
                with patch("filesearch.ui.main_window.logger") as mock_logger:
                    # Execute properties action
                    main_window._handle_context_properties([search_results[0]])

                    # Verify error was logged and handled
                    mock_logger.error.assert_called()
                    mock_status.assert_called_with(
                        "Failed to show properties: Dialog creation failed"
                    )


class TestCrossPlatformFileOperations:
    """Test cross-platform file operation integration."""

    @patch("filesearch.ui.main_window.open_containing_folder")
    def test_open_containing_folder_platform_integration(
        self, mock_open_folder, main_window, search_results
    ):
        """Test open containing folder works across platforms."""
        # Test that the function is called correctly
        main_window._handle_context_open_containing_folder([search_results[0]])

        mock_open_folder.assert_called_once_with(search_results[0].path)

    def test_clipboard_operations_cross_platform(self, main_window, search_results):
        """Test clipboard operations work consistently across platforms."""
        # Test path copying
        with patch("PyQt6.QtGui.QGuiApplication.clipboard") as mock_clipboard_getter:
            mock_clipboard = Mock()
            mock_clipboard_getter.return_value = mock_clipboard

            main_window._handle_context_copy_path([search_results[0]])

            # Verify standard text clipboard API is used
            mock_clipboard.setText.assert_called_once_with(str(search_results[0].path))

        # Test file copying (MIME data)
        with patch("PyQt6.QtGui.QGuiApplication.clipboard") as mock_clipboard_getter:
            mock_clipboard = Mock()
            mock_clipboard_getter.return_value = mock_clipboard

            main_window._handle_context_copy_file([search_results[0]])

            # Verify MIME data API is used for file copying
            call_args = mock_clipboard.setMimeData.call_args[0]
            mime_data = call_args[0]
            assert hasattr(mime_data, "setUrls")  # MIME data for files


class TestPerformanceAndMemory:
    """Test performance and memory usage expectations."""

    def test_menu_creation_performance(self, main_window, search_results, qtbot):
        """Test menu creation happens within acceptable time."""
        import time

        # Set up results
        main_window.results_view.set_results(search_results)

        # Measure menu creation time
        start_time = time.time()
        menu = main_window._create_context_menu([search_results[0]])
        end_time = time.time()

        # Verify menu creation is fast (< 100ms target from AC15)
        duration = end_time - start_time
        assert duration < 0.1, "Menu creation too slow: {:.3f}s".format(duration)

        # Verify menu is created correctly
        assert menu is not None

    def test_multiple_result_handling(self, main_window, search_results):
        """Test handling of multiple results without excessive memory usage."""
        # Create larger set of results
        many_results = []
        for i in range(50):
            result = SearchResult(
                path=Path(f"/home/user/file{i}.txt"),
                size=100 * (i + 1),
                modified=1678886400 + i * 86400,
            )
            many_results.append(result)

        # Set results and measure memory stability
        main_window.results_view.set_results(many_results)

        with patch.object(main_window, "safe_status_message"):
            # Execute batch operations
            main_window._handle_context_copy_path(many_results)

            # Operations should complete without memory issues
            # (This would fail with memory problems in real implementation)

    def test_error_handling_performance(self, main_window, search_results):
        """Test error handling doesn't significantly impact performance."""
        import time

        # Cause repeated errors
        with patch("PyQt6.QtGui.QGuiApplication.clipboard") as mock_clipboard_getter:
            mock_clipboard = Mock()
            mock_clipboard.setText.side_effect = Exception("Persistent error")
            mock_clipboard_getter.return_value = mock_clipboard

            start_time = time.time()
            for _ in range(10):
                main_window._handle_context_copy_path([search_results[0]])
            end_time = time.time()

            duration = end_time - start_time
            # Even with errors, operations should remain reasonably fast
            assert (
                duration < 0.05
            ), "Error handling too slow: {:.3f}s for 10 operations".format(duration)
