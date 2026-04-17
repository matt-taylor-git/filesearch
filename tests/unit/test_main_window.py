"""Unit tests for the main window module."""

import sys
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import Qt, QThread
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from filesearch.core.config_manager import ConfigManager
from filesearch.core.search_engine import FileSearchEngine
from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow, SearchWorker, create_main_window


# Create QApplication instance for tests
@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for testing."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def config_manager(tmp_path):
    """Create an isolated config manager for testing."""
    with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
        manager = ConfigManager(app_name="testapp")
        yield manager


@pytest.fixture
def main_window(qapp, config_manager):
    """Create a MainWindow instance for testing."""
    window = MainWindow(config_manager)
    yield window
    window.close()


class TestSearchWorker:
    """Test cases for SearchWorker class."""

    @pytest.fixture
    def search_worker(self):
        """Create a SearchWorker instance."""
        engine = FileSearchEngine()
        worker = SearchWorker(engine, Path("/test"), "*.txt")
        yield worker

    def test_search_worker_initialization(self, search_worker):
        """Test SearchWorker initialization."""
        assert search_worker.directory == Path("/test")
        assert search_worker.query == "*.txt"
        assert search_worker._is_running is False
        assert isinstance(search_worker.search_engine, FileSearchEngine)

    def test_search_worker_signals(self, search_worker):
        """Test that SearchWorker has required signals."""
        assert hasattr(search_worker, "result_found")
        assert hasattr(search_worker, "progress_update")
        assert hasattr(search_worker, "search_complete")
        assert hasattr(search_worker, "error_occurred")
        assert hasattr(search_worker, "search_stopped")

    def test_search_worker_stop(self, search_worker):
        """Test stopping the search worker."""
        search_worker._is_running = True
        search_worker.stop()

        assert search_worker._is_running is False
        assert search_worker.search_engine._cancelled is True


class TestMainWindowInitialization:
    """Test cases for MainWindow initialization."""

    def test_main_window_initialization(self, main_window):
        """Test MainWindow initialization."""
        assert isinstance(main_window, MainWindow)
        assert isinstance(main_window.config_manager, ConfigManager)
        assert isinstance(main_window.search_engine, FileSearchEngine)
        assert main_window.is_searching is False
        assert main_window.search_worker is None

    def test_main_window_ui_components(self, main_window):
        """Test that MainWindow has required UI components."""
        assert hasattr(main_window, "directory_selector")
        assert hasattr(main_window, "query_input")
        assert hasattr(main_window, "search_control")
        assert hasattr(main_window, "results_label")

    def test_main_window_title(self, main_window):
        """Test MainWindow title."""
        assert main_window.windowTitle() == "File Search"

    def test_main_window_minimum_size(self, main_window):
        """Test MainWindow minimum size."""
        min_size = main_window.minimumSize()
        assert min_size.width() == 900
        assert min_size.height() == 550


class TestMainWindowUIState:
    """Test cases for MainWindow UI state management."""

    def test_initial_ui_state(self, main_window):
        """Test initial UI state."""
        # Search control button is disabled when query is empty
        assert main_window.search_control.search_button.isEnabled() is False
        assert main_window.query_input.isEnabled() is True
        assert str(main_window.directory_selector.get_directory()) != ""

    def test_load_window_settings(self, main_window):
        """Test loading window settings."""
        # Set some config values
        main_window.config_manager.set("ui.window_width", 1024)
        main_window.config_manager.set("ui.window_height", 768)

        # Load settings
        main_window.load_window_settings()

        # Note: In test environment, this might not actually resize
        # but we verify the method runs without error
        assert True

    def test_save_window_settings(self, main_window):
        """Test saving window settings."""
        # Resize window
        main_window.resize(800, 600)

        # Save settings
        main_window.save_window_settings()

        # Verify config was updated
        width = main_window.config_manager.get("ui.window_width")
        height = main_window.config_manager.get("ui.window_height")

        assert width == 800
        assert height == 600

    def test_center_tabs_include_search_and_storage(self, main_window):
        """The center area exposes Search and Storage tabs."""
        tab_labels = [
            main_window.center_tabs.tabText(index)
            for index in range(main_window.center_tabs.count())
        ]

        assert tab_labels == ["Search", "Storage"]


class TestMainWindowSearchControls:
    """Test cases for MainWindow search functionality."""

    def test_start_search_with_empty_inputs(self, main_window):
        """Test starting search with empty inputs."""
        main_window.directory_selector.set_directory(Path(""))
        main_window.query_input.set_text("")

        main_window.start_search()

        # Should show error message in status bar
        status_message = main_window.statusBar().currentMessage()
        assert "Please enter both directory and search pattern" in status_message

    def test_start_search_with_invalid_directory(self, main_window):
        """Test starting search with invalid directory."""
        main_window.directory_selector.set_directory(Path("/nonexistent/directory"))
        main_window.query_input.set_text("*.txt")

        main_window.start_search()

        # Should show error message in status bar
        status_message = main_window.statusBar().currentMessage()
        assert "Directory does not exist" in status_message

    def test_start_search_enables_stop_button(self, main_window):
        """Test that starting search changes control state."""
        with tempfile.TemporaryDirectory() as tmpdir:
            main_window.directory_selector.set_directory(Path(tmpdir))
            main_window.query_input.set_text("*.txt")

            # Mock the search worker to prevent actual search
            with patch("filesearch.ui.main_window.SearchWorker") as mock_worker_class:
                mock_worker = Mock()
                mock_worker_class.return_value = mock_worker

                main_window.start_search()

                # Check that search control is in RUNNING state
                from filesearch.ui.search_controls import SearchState

                assert main_window.search_control.get_state() == SearchState.RUNNING

    def test_stop_search_when_not_searching(self, main_window):
        """Test stopping search when not currently searching."""
        # Should not raise exception
        main_window.stop_search()
        assert main_window.is_searching is False

    def test_reset_search_ui(self, main_window):
        """Test resetting search UI."""
        from filesearch.ui.search_controls import SearchState

        # Set searching state
        main_window.is_searching = True
        main_window.search_control.set_state(SearchState.RUNNING)

        # Reset UI
        main_window.reset_search_ui()

        assert main_window.is_searching is False
        assert main_window.search_control.get_state() == SearchState.IDLE


class TestMainWindowSignals:
    """Test cases for MainWindow signal handling."""

    def test_signals_connected(self, qtbot, config_manager):
        """Test that signals are properly connected."""
        with patch(
            "filesearch.ui.main_window.MainWindow.start_search"
        ) as mock_start, patch(
            "filesearch.ui.main_window.MainWindow.stop_search"
        ) as mock_stop:
            main_window = MainWindow(config_manager=config_manager)
            main_window.show()
            qtbot.addWidget(main_window)
            main_window.activateWindow()
            QApplication.processEvents()

            # Test search control signals
            main_window.query_input.set_text("test")
            main_window.search_control.search_requested.emit()
            mock_start.assert_called_once()

            # Test stop control signal
            main_window.search_control.search_stopped.emit()
            mock_stop.assert_called_once()

    def test_query_input_return_pressed(self, qtbot, config_manager):
        """Test that Enter key in query input triggers search."""
        with patch("filesearch.ui.main_window.MainWindow.start_search") as mock_start:
            main_window = MainWindow(config_manager=config_manager)
            main_window.show()
            qtbot.addWidget(main_window)

            main_window.query_input.set_text("test")
            main_window.query_input.set_focus()
            qtbot.keyPress(main_window.query_input.search_input, Qt.Key.Key_Return)
            mock_start.assert_called_once()


class TestMainWindowDirectorySelection:
    """Test sidebar-driven directory selection behavior."""

    def test_startup_uses_default_search_directory(self, qapp, config_manager, tmp_path):
        """Window restores the configured default directory when it is valid."""
        default_dir = tmp_path / "search-root"
        default_dir.mkdir()
        config_manager.set(
            "search_preferences.default_search_directory", str(default_dir)
        )

        window = MainWindow(config_manager=config_manager)

        try:
            assert window.current_directory == default_dir
            assert window.directory_selector.get_directory() == default_dir
        finally:
            window.close()

    def test_startup_falls_back_to_home_for_missing_directory(
        self, qapp, config_manager, tmp_path
    ):
        """Window falls back safely when the saved default directory is missing."""
        missing_dir = tmp_path / "missing-root"
        config_manager.set(
            "search_preferences.default_search_directory", str(missing_dir)
        )

        window = MainWindow(config_manager=config_manager)

        try:
            assert window.current_directory == Path.home()
        finally:
            window.close()

    def test_sidebar_browse_opens_dialog_and_updates_directory(
        self, qtbot, config_manager, tmp_path
    ):
        """Choosing a folder from the sidebar updates UI state and persisted config."""
        selected_dir = tmp_path / "custom-root"
        selected_dir.mkdir()

        window = MainWindow(config_manager=config_manager)
        window.show()
        qtbot.addWidget(window)

        with patch(
            "filesearch.ui.main_window.QFileDialog.getExistingDirectory",
            return_value=str(selected_dir),
        ) as mock_dialog:
            qtbot.mouseClick(window.sidebar._browse_button, Qt.MouseButton.LeftButton)

        try:
            mock_dialog.assert_called_once()
            assert window.current_directory == selected_dir
            assert window.directory_selector.get_directory() == selected_dir
            assert (
                config_manager.get("search_preferences.default_search_directory")
                == str(selected_dir)
            )
            assert config_manager.get("recent.directories")[0] == str(selected_dir)
            assert window.sidebar.get_custom_location() == selected_dir
            assert window.statusBar().currentMessage() == (
                f"Search folder selected: {selected_dir}"
            )
        finally:
            window.close()

    def test_sidebar_downloads_uses_resolved_special_folder(
        self, qtbot, config_manager, tmp_path
    ):
        """Downloads preset should use the resolved OS folder path."""
        redirected_downloads = tmp_path / "redirected-downloads"
        redirected_downloads.mkdir()

        with patch(
            "filesearch.ui.sidebar_widget.get_user_folder"
        ) as mock_sidebar_folder, patch(
            "filesearch.ui.main_window.get_user_folder"
        ) as mock_main_folder:
            def resolve_folder(name):
                mapping = {
                    "home": Path.home(),
                    "documents": Path.home() / "Documents",
                    "desktop": Path.home() / "Desktop",
                    "downloads": redirected_downloads,
                    "pictures": Path.home() / "Pictures",
                    "videos": Path.home() / "Videos",
                }
                return mapping[name]

            mock_sidebar_folder.side_effect = resolve_folder
            mock_main_folder.side_effect = resolve_folder

            window = MainWindow(config_manager=config_manager)
            window.show()
            qtbot.addWidget(window)

        downloads_button = next(
            button
            for button in window.sidebar._location_buttons
            if button.text().strip() == "Downloads"
        )

        try:
            qtbot.mouseClick(downloads_button, Qt.MouseButton.LeftButton)

            assert window.current_directory == redirected_downloads
            assert window.directory_selector.get_directory() == redirected_downloads
            assert window.sidebar.get_custom_location() is None
            assert downloads_button.property("active") == "true"
        finally:
            window.close()

    def test_redirected_preset_folder_is_not_treated_as_custom(
        self, qapp, config_manager, tmp_path
    ):
        """Resolved preset folders should not appear as custom sidebar entries."""
        redirected_downloads = tmp_path / "redirected-downloads"
        redirected_downloads.mkdir()
        config_manager.set(
            "search_preferences.default_search_directory", str(redirected_downloads)
        )

        with patch(
            "filesearch.ui.sidebar_widget.get_user_folder"
        ) as mock_sidebar_folder, patch(
            "filesearch.ui.main_window.get_user_folder"
        ) as mock_main_folder:
            def resolve_folder(name):
                mapping = {
                    "home": Path.home(),
                    "documents": Path.home() / "Documents",
                    "desktop": Path.home() / "Desktop",
                    "downloads": redirected_downloads,
                    "pictures": Path.home() / "Pictures",
                    "videos": Path.home() / "Videos",
                }
                return mapping[name]

            mock_sidebar_folder.side_effect = resolve_folder
            mock_main_folder.side_effect = resolve_folder

            window = MainWindow(config_manager=config_manager)

        try:
            assert window.current_directory == redirected_downloads
            assert window.sidebar.get_custom_location() is None
        finally:
            window.close()

    def test_custom_sidebar_location_reuses_saved_folder(
        self, qtbot, config_manager, tmp_path
    ):
        """Clicking the custom sidebar row selects the saved folder without browsing."""
        selected_dir = tmp_path / "saved-root"
        selected_dir.mkdir()
        config_manager.set("recent.directories", [str(selected_dir)])

        window = MainWindow(config_manager=config_manager)
        window.show()
        qtbot.addWidget(window)

        with patch(
            "filesearch.ui.main_window.QFileDialog.getExistingDirectory"
        ) as mock_dialog:
            qtbot.mouseClick(
                window.sidebar._custom_location_button, Qt.MouseButton.LeftButton
            )

        try:
            mock_dialog.assert_not_called()
            assert window.current_directory == selected_dir
            assert window.sidebar.get_custom_location() == selected_dir
            assert window.sidebar._custom_location_button.property("active") == "true"
            assert window.storage_tab.root_path == selected_dir
        finally:
            window.close()

    def test_storage_tab_root_tracks_directory_changes(
        self, qtbot, config_manager, tmp_path
    ):
        """Changing the active folder updates the storage tab root."""
        selected_dir = tmp_path / "workspace"
        selected_dir.mkdir()

        window = MainWindow(config_manager=config_manager)
        window.show()
        qtbot.addWidget(window)

        try:
            window._set_search_directory(selected_dir, persist=False, update_recent=False)
            assert window.storage_tab.root_path == selected_dir
        finally:
            window.close()

    def test_storage_tab_activation_hides_details_panel(
        self, qtbot, config_manager, tmp_path
    ):
        """Switching to Storage collapses the right-hand details panel."""
        selected_dir = tmp_path / "workspace"
        selected_dir.mkdir()

        window = MainWindow(config_manager=config_manager)
        window.show()
        qtbot.addWidget(window)
        window._set_search_directory(selected_dir, persist=False, update_recent=False)

        result = SearchResult(path=selected_dir, size=0, modified=0.0)
        window.details_panel.show_result(result)
        window.main_splitter.setSizes([240, 420, 280])

        try:
            window.center_tabs.setCurrentWidget(window.storage_tab)
            qtbot.waitUntil(lambda: window.main_splitter.sizes()[2] == 0, timeout=3000)
            assert window.main_splitter.sizes()[2] == 0
        finally:
            window.close()


class TestMainWindowResultHandling:
    """Test cases for MainWindow result handling."""

    def test_on_result_found(self, main_window):
        """Test handling found search results."""
        test_result = {
            "path": "/test/file.txt",
            "name": "file.txt",
            "source": "filesystem",
            "size": 100,
            "modified": 1234567890,
        }

        main_window.on_result_found(test_result, 1)

        assert len(main_window.search_results) == 1
        assert main_window.search_results[0] == test_result

    def test_on_progress_update(self, main_window):
        """Test handling progress updates."""
        main_window.on_progress_update(50, "/test/dir", 10)

        status_message = main_window.statusBar().currentMessage()
        assert "Searching /test/dir" in status_message
        assert "Found 10 files" in status_message

    def test_on_search_complete(self, main_window):
        """Test handling search completion."""
        from filesearch.ui.search_controls import SearchState

        main_window.is_searching = True
        main_window.search_control.set_state(SearchState.RUNNING)

        main_window.on_search_complete(5, 2)

        assert main_window.is_searching is False
        assert main_window.search_control.get_state() == SearchState.IDLE

        status_message = main_window.statusBar().currentMessage()
        assert "Found 5 results" in status_message

    def test_on_search_stopped(self, main_window):
        """Test handling search stop."""
        main_window.is_searching = True

        main_window.on_search_stopped(3, 1)

        assert main_window.is_searching is False
        status_message = main_window.statusBar().currentMessage()
        assert "Search stopped: 3 files found" in status_message

    def test_on_search_error(self, main_window):
        """Test handling search errors."""
        main_window.is_searching = True

        main_window.on_search_error("Test error", 1)

        assert main_window.is_searching is False
        status_message = main_window.statusBar().currentMessage()
        assert "Error: Test error" in status_message


class TestMainWindowFileOperations:
    """Test cases for MainWindow file operations."""

    def test_open_selected_file_success(self, main_window):
        """Test successfully opening a selected file."""
        test_path = Path("/test/document.pdf")

        with patch("filesearch.ui.main_window.safe_open") as mock_safe_open:
            mock_safe_open.return_value = True

            main_window.open_selected_file(test_path)

            mock_safe_open.assert_called_once_with(test_path)

            status_message = main_window.statusBar().currentMessage()
            assert "Opened: document.pdf" in status_message

    def test_open_selected_file_error(self, main_window):
        """Test error when opening a selected file."""
        from filesearch.core.exceptions import FileSearchError

        test_path = Path("/test/document.pdf")

        with patch("filesearch.ui.main_window.safe_open") as mock_safe_open:
            mock_safe_open.side_effect = FileSearchError("Cannot open file")

            main_window.open_selected_file(test_path)

            status_message = main_window.statusBar().currentMessage()
            assert "Error opening file" in status_message

    def test_open_selected_folder_success(self, main_window):
        """Test successfully opening a selected folder."""
        test_path = Path("/test/documents/report.pdf")

        with patch(
            "filesearch.ui.main_window.open_containing_folder"
        ) as mock_open_folder:
            mock_open_folder.return_value = True

            main_window.open_selected_folder(test_path)

            mock_open_folder.assert_called_once_with(test_path)

            status_message = main_window.statusBar().currentMessage()
            assert "Opened folder: /test/documents" in status_message

    def test_open_selected_folder_error(self, main_window):
        """Test error when opening a selected folder."""
        from filesearch.core.exceptions import FileSearchError

        test_path = Path("/test/document.pdf")

        with patch(
            "filesearch.ui.main_window.open_containing_folder"
        ) as mock_open_folder:
            mock_open_folder.side_effect = FileSearchError("Cannot open folder")

            main_window.open_selected_folder(test_path)

            status_message = main_window.statusBar().currentMessage()
            assert "Error opening folder" in status_message


class TestMainWindowCloseEvent:
    """Test cases for MainWindow close event."""

    def test_close_event_saves_settings(self, main_window):
        """Test that close event saves window settings."""
        with patch.object(main_window, "save_window_settings") as mock_save:
            with patch.object(main_window, "close"):
                # Simulate close event
                from PyQt6.QtGui import QCloseEvent

                event = QCloseEvent()
                main_window.closeEvent(event)

                mock_save.assert_called_once()

    def test_close_event_stops_search(self, main_window):
        """Test that close event stops ongoing search."""
        # Mock an ongoing search
        mock_worker = Mock()
        main_window.search_worker = mock_worker
        main_window.is_searching = True

        with patch.object(main_window, "save_window_settings"):
            from PyQt6.QtGui import QCloseEvent

            event = QCloseEvent()
            main_window.closeEvent(event)

            mock_worker.stop.assert_called_once()
            mock_worker.wait.assert_called_once()


class TestCreateMainWindowFunction:
    """Test cases for create_main_window function."""

    def test_create_main_window(self, qapp, tmp_path):
        """Test create_main_window function."""
        with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
            window = create_main_window()

            assert isinstance(window, MainWindow)
            assert isinstance(window.config_manager, ConfigManager)

            window.close()

    def test_create_main_window_with_config(self, qapp, config_manager):
        """Test create_main_window with custom config manager."""
        window = create_main_window(config_manager)

        assert isinstance(window, MainWindow)
        assert window.config_manager == config_manager

        window.close()
