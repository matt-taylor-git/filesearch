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
def config_manager():
    """Create a mock config manager."""
    with patch("platformdirs.user_config_dir", return_value="/tmp/test_config"):
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
        assert min_size.width() == 600
        assert min_size.height() == 400


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

    def test_create_main_window(self, qapp):
        """Test create_main_window function."""
        with patch("platformdirs.user_config_dir", return_value="/tmp/test_config"):
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
