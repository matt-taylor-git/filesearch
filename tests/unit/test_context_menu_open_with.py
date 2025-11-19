"""Unit tests for Open With context menu functionality."""

from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


@pytest.fixture
def search_result():
    return SearchResult(
        path=Path("/home/user/file1.txt"),
        size=100,
        modified=1678886400,
    )


class TestOpenWithMenu:
    """Test the Open With submenu functionality."""

    @patch("filesearch.ui.main_window.get_associated_applications")
    def test_populate_open_with_menu(self, mock_get_apps, search_result):
        """Test populating the Open With menu."""
        # Mock associated applications
        mock_get_apps.return_value = [
            {
                "name": "Text Editor",
                "id": "org.gnome.TextEditor.desktop",
                "type": "desktop_id",
            },
            {"name": "Vim", "id": "vim.desktop", "type": "desktop_id"},
        ]

        window = Mock(spec=MainWindow)
        window._handle_open_with_app = Mock()
        window._handle_choose_application = Mock()

        # Bind method
        window._populate_open_with_menu = MainWindow._populate_open_with_menu.__get__(
            window, MainWindow
        )

        menu = Mock()

        window._populate_open_with_menu(menu, search_result)

        # Verify menu was cleared
        menu.clear.assert_called_once()

        # Verify actions were added (2 apps + separator + choose...)
        # Note: addAction returns an action, so we can't count calls easily if we don't track return values
        # But we can check call count for addAction
        assert menu.addAction.call_count == 3  # Text Editor, Vim, Choose...
        menu.addSeparator.assert_called_once()

    @patch("filesearch.ui.main_window.open_with_application")
    def test_handle_open_with_app(self, mock_open_with, search_result):
        """Test handling opening with specific app."""
        window = Mock(spec=MainWindow)
        window.safe_status_message = Mock()

        window._handle_open_with_app = MainWindow._handle_open_with_app.__get__(
            window, MainWindow
        )

        app_info = {"name": "Text Editor", "id": "org.gnome.TextEditor.desktop"}

        window._handle_open_with_app(app_info, search_result)

        mock_open_with.assert_called_once_with(search_result.path, app_info)
        window.safe_status_message.assert_any_call(
            f"Opening {search_result.path.name} with Text Editor..."
        )

    @patch("PyQt6.QtWidgets.QFileDialog")
    def test_handle_choose_application(self, mock_file_dialog_class, search_result):
        """Test choosing application from dialog."""
        window = Mock(spec=MainWindow)
        window._handle_open_with_app = Mock()

        # Mock dialog interaction
        mock_dialog = mock_file_dialog_class.return_value
        mock_dialog.exec.return_value = True
        mock_dialog.selectedFiles.return_value = ["/usr/bin/gedit"]

        window._handle_choose_application = (
            MainWindow._handle_choose_application.__get__(window, MainWindow)
        )

        window._handle_choose_application(search_result)

        # Verify handle_open_with_app was called with correct info
        expected_app_info = {"name": "gedit", "command": "/usr/bin/gedit"}
        window._handle_open_with_app.assert_called_once_with(
            expected_app_info, search_result
        )

    @patch("PyQt6.QtWidgets.QFileDialog")
    def test_handle_choose_application_cancelled(
        self, mock_file_dialog_class, search_result
    ):
        """Test choosing application cancelled."""
        window = Mock(spec=MainWindow)
        window._handle_open_with_app = Mock()

        # Mock dialog cancellation
        mock_dialog = mock_file_dialog_class.return_value
        mock_dialog.exec.return_value = False

        window._handle_choose_application = (
            MainWindow._handle_choose_application.__get__(window, MainWindow)
        )

        window._handle_choose_application(search_result)

        window._handle_open_with_app.assert_not_called()
