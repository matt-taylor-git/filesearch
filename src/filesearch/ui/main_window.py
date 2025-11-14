"""Main GUI window module for the file search application.

This module provides the MainWindow class that implements the main user interface
with search input, directory selection, and results display functionality.
"""

from pathlib import Path
from typing import Optional

from loguru import logger
from PyQt6.QtCore import Qt, QThread, pyqtSignal  # noqa: F401
from PyQt6.QtWidgets import QApplication  # noqa: F401
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import open_containing_folder, safe_open
from filesearch.core.search_engine import FileSearchEngine


class SearchWorker(QThread):
    """Worker thread for performing file searches in the background.

    This class handles search operations in a separate thread to keep the UI
    responsive during searches.

    Signals:
        result_found(Path, int): Emitted when a matching file is found
        progress_update(int, str, int): Emitted for search progress updates
        search_complete(int, int): Emitted when search is complete
        error_occurred(str, int): Emitted when an error occurs
        search_stopped(int, int): Emitted when search is stopped
    """

    result_found = pyqtSignal(Path, int)  # path, result_number
    progress_update = pyqtSignal(
        int, str, int
    )  # progress_percent, current_dir, files_found
    search_complete = pyqtSignal(int, int)  # total_files, total_dirs
    error_occurred = pyqtSignal(str, int)  # error_message, error_code
    search_stopped = pyqtSignal(int, int)  # files_found, dirs_searched

    def __init__(self, search_engine: FileSearchEngine, directory: Path, query: str):
        """Initialize the search worker.

        Args:
            search_engine: FileSearchEngine instance
            directory: Directory to search in
            query: Search pattern
        """
        super().__init__()
        self.search_engine = search_engine
        self.directory = directory
        self.query = query
        self._is_running = False

        logger.debug(f"SearchWorker initialized for {directory} with query '{query}'")

    def run(self) -> None:
        """Execute the search operation."""
        self._is_running = True
        files_found = 0
        dirs_searched = 0

        try:
            logger.info(f"Starting search in {self.directory} for '{self.query}'")

            # Perform the search
            for result_path in self.search_engine.search(self.directory, self.query):
                if not self._is_running:
                    break

                files_found += 1
                self.result_found.emit(result_path, files_found)

                # Update progress periodically
                if files_found % 10 == 0:
                    self.progress_update.emit(50, str(self.directory), files_found)

            if self._is_running:
                self.search_complete.emit(files_found, dirs_searched)
                logger.info(f"Search completed: {files_found} files found")
            else:
                self.search_stopped.emit(files_found, dirs_searched)
                logger.info(f"Search stopped: {files_found} files found")

        except FileSearchError as e:
            logger.error(f"Search error: {e}")
            self.error_occurred.emit(str(e), 1)
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            self.error_occurred.emit(f"Unexpected error: {e}", 2)

    def stop(self) -> None:
        """Stop the search operation."""
        self._is_running = False
        self.search_engine.cancel()
        logger.info("SearchWorker stop requested")


class MainWindow(QMainWindow):
    """Main application window for the file search tool.

    This class implements the main GUI with search controls, directory selection,
    and results display. It uses an event-driven architecture with signals/slots
    for thread-safe communication.

    Attributes:
        config_manager (ConfigManager): Configuration manager instance
        search_engine (FileSearchEngine): Search engine instance
        search_worker (Optional[SearchWorker]): Current search worker thread
        is_searching (bool): Whether a search is currently active
    """

    def __init__(self, config_manager: Optional[ConfigManager] = None):
        """Initialize the main window.

        Args:
            config_manager: Configuration manager instance (creates default if None)
        """
        super().__init__()

        # Initialize components
        self.config_manager = config_manager or ConfigManager()
        self.search_engine = FileSearchEngine(config_manager=self.config_manager)
        self.search_worker: Optional[SearchWorker] = None
        self.is_searching = False
        self.search_results = []

        # Setup UI
        self.setup_ui()
        self.connect_signals()
        self.load_window_settings()

        logger.info("MainWindow initialized")

    def setup_ui(self) -> None:
        """Setup the user interface components."""
        # Set window properties
        self.setWindowTitle("File Search")
        self.setMinimumSize(600, 400)

        # Create menu bar
        settings_menu = self.menuBar().addMenu("Settings")
        settings_menu.addAction("Preferences...", self.show_settings_dialog)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create search controls layout
        search_layout = QHBoxLayout()

        # Directory selection
        self.dir_label = QLabel("Directory:")
        self.dir_input = QLineEdit()
        self.dir_input.setText(
            self.config_manager.get(
                "search_preferences.default_search_directory", str(Path.home())
            )
        )
        self.dir_input.setPlaceholderText("Enter directory path...")

        self.browse_button = QPushButton("Browse...")

        search_layout.addWidget(self.dir_label)
        search_layout.addWidget(self.dir_input)
        search_layout.addWidget(self.browse_button)

        # Search query layout
        query_layout = QHBoxLayout()

        self.query_label = QLabel("Search:")
        self.query_input = QLineEdit()
        self.query_input.setPlaceholderText(
            "Enter search pattern (e.g., *.py, document*)"
        )

        self.search_button = QPushButton("Search")
        self.stop_button = QPushButton("Stop")
        self.stop_button.setEnabled(False)

        query_layout.addWidget(self.query_label)
        query_layout.addWidget(self.query_input)
        query_layout.addWidget(self.search_button)
        query_layout.addWidget(self.stop_button)

        # Add layouts to main layout
        main_layout.addLayout(search_layout)
        main_layout.addLayout(query_layout)

        # Results area (placeholder for now)
        self.results_label = QLabel("Results:")
        main_layout.addWidget(self.results_label)

        # Status bar
        self.statusBar().showMessage("Ready")

        logger.debug("UI setup completed")

    def connect_signals(self) -> None:
        """Connect signals and slots for event handling."""
        # Search controls
        self.search_button.clicked.connect(self.start_search)
        self.stop_button.clicked.connect(self.stop_search)
        self.browse_button.clicked.connect(self.browse_directory)

        # Enter key triggers search
        self.query_input.returnPressed.connect(self.start_search)

        logger.debug("Signals connected")

    def load_window_settings(self) -> None:
        """Load window settings from configuration."""
        try:
            # Load window size
            width = self.config_manager.get("ui.window_width", 800)
            height = self.config_manager.get("ui.window_height", 600)
            self.resize(width, height)

            logger.debug(f"Window settings loaded: {width}x{height}")

        except Exception as e:
            logger.error(f"Error loading window settings: {e}")

    def save_window_settings(self) -> None:
        """Save window settings to configuration."""
        try:
            # Save window size
            self.config_manager.set("ui.window_width", self.width())
            self.config_manager.set("ui.window_height", self.height())
            self.config_manager.save()

            logger.debug("Window settings saved")

        except Exception as e:
            logger.error(f"Error saving window settings: {e}")

    def browse_directory(self) -> None:
        """Open directory browser dialog."""
        # Note: This is a simplified version
        # In a full implementation, you'd use QFileDialog
        current_dir = self.dir_input.text()
        self.statusBar().showMessage(f"Browse directory: {current_dir}")
        logger.info(f"Browse directory requested: {current_dir}")

    def start_search(self) -> None:
        """Start the file search operation."""
        if self.is_searching:
            logger.warning("Search already in progress")
            return

        # Get search parameters
        directory = Path(self.dir_input.text().strip())
        query = self.query_input.text().strip()

        # Validate inputs
        if not directory or not query:
            self.statusBar().showMessage(
                "Please enter both directory and search pattern"
            )
            return

        if not directory.exists():
            self.statusBar().showMessage(f"Directory does not exist: {directory}")
            return

        # Clear previous results
        self.search_results.clear()

        # Update UI state
        self.is_searching = True
        self.search_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.query_input.setEnabled(False)
        self.statusBar().showMessage(f"Searching for '{query}' in {directory}...")

        # Create and start search worker
        self.search_worker = SearchWorker(self.search_engine, directory, query)

        # Connect worker signals
        self.search_worker.result_found.connect(self.on_result_found)
        self.search_worker.progress_update.connect(self.on_progress_update)
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.search_stopped.connect(self.on_search_stopped)

        # Start search
        self.search_worker.start()
        logger.info(f"Search started: '{query}' in {directory}")

    def stop_search(self) -> None:
        """Stop the current search operation."""
        if not self.is_searching or not self.search_worker:
            return

        self.search_worker.stop()
        self.statusBar().showMessage("Stopping search...")
        logger.info("Search stop requested")

    def on_result_found(self, path: Path, result_number: int) -> None:
        """Handle search result found signal.

        Args:
            path: Path to the found file
            result_number: Result number
        """
        self.search_results.append(path)

        # Update status periodically
        if result_number % 10 == 0:
            self.statusBar().showMessage(f"Found {result_number} files...")

        logger.debug(f"Result found: {path} (#{result_number})")

    def on_progress_update(
        self, progress: int, current_dir: str, files_found: int
    ) -> None:
        """Handle progress update signal.

        Args:
            progress: Progress percentage
            current_dir: Current directory being searched
            files_found: Number of files found so far
        """
        self.statusBar().showMessage(
            f"Searching {current_dir}... Found {files_found} files"
        )
        logger.debug(f"Progress: {progress}% in {current_dir}, {files_found} files")

    def on_search_complete(self, total_files: int, total_dirs: int) -> None:
        """Handle search complete signal.

        Args:
            total_files: Total files found
            total_dirs: Total directories searched
        """
        self.reset_search_ui()
        self.statusBar().showMessage(f"Search complete: {total_files} files found")
        logger.info(
            f"Search completed: {total_files} files in {total_dirs} directories"
        )

    def on_search_stopped(self, files_found: int, dirs_searched: int) -> None:
        """Handle search stopped signal.

        Args:
            files_found: Files found before stopping
            dirs_searched: Directories searched before stopping
        """
        self.reset_search_ui()
        self.statusBar().showMessage(f"Search stopped: {files_found} files found")
        logger.info(
            f"Search stopped: {files_found} files in {dirs_searched} directories"
        )

    def on_search_error(self, error_message: str, error_code: int) -> None:
        """Handle search error signal.

        Args:
            error_message: Error message
            error_code: Error code
        """
        self.reset_search_ui()
        self.statusBar().showMessage(f"Search error: {error_message}")
        logger.error(f"Search error {error_code}: {error_message}")

    def reset_search_ui(self) -> None:
        """Reset UI to ready state after search completes."""
        self.is_searching = False
        self.search_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.query_input.setEnabled(True)

        if self.search_worker:
            self.search_worker = None

        logger.debug("Search UI reset")

    def open_selected_file(self, file_path: Path) -> None:
        """Open the selected file with default application.

        Args:
            file_path: Path to the file to open
        """
        try:
            safe_open(file_path)
            self.statusBar().showMessage(f"Opened: {file_path.name}")
            logger.info(f"Opened file: {file_path}")
        except FileSearchError as e:
            self.statusBar().showMessage(f"Error opening file: {e}")
            logger.error(f"Error opening file {file_path}: {e}")

    def open_selected_folder(self, file_path: Path) -> None:
        """Open the containing folder of selected file.

        Args:
            file_path: Path to the file
        """
        try:
            open_containing_folder(file_path)
            self.statusBar().showMessage(f"Opened folder: {file_path.parent}")
            logger.info(f"Opened folder: {file_path.parent}")
        except FileSearchError as e:
            self.statusBar().showMessage(f"Error opening folder: {e}")
            logger.error(f"Error opening folder for {file_path}: {e}")

    def show_settings_dialog(self) -> None:
        """Show the settings dialog."""
        try:
            from filesearch.ui.settings_dialog import SettingsDialog

            dialog = SettingsDialog(self.config_manager, self)
            dialog.exec()
            logger.info("Settings dialog shown")
        except Exception as e:
            self.statusBar().showMessage(f"Error opening settings: {e}")
            logger.error(f"Error opening settings dialog: {e}")

    def closeEvent(self, event) -> None:
        """Handle window close event.

        Args:
            event: Close event
        """
        # Stop any ongoing search
        if self.is_searching and self.search_worker:
            self.search_worker.stop()
            self.search_worker.wait()

        # Save window settings
        self.save_window_settings()

        logger.info("MainWindow closing")
        event.accept()


def create_main_window(config_manager: Optional[ConfigManager] = None) -> MainWindow:
    """Create and return the main application window.

    Args:
        config_manager: Configuration manager instance

    Returns:
        MainWindow instance

    Example:
        >>> from PyQt6.QtWidgets import QApplication
        >>> app = QApplication([])
        >>> window = create_main_window()
        >>> window.show()
        >>> app.exec()
    """
    return MainWindow(config_manager)
