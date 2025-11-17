"""Main GUI window module for the file search application.

This module provides the MainWindow class that implements the main user interface
with search input, directory selection, and results display functionality.
"""

import time
from pathlib import Path
from typing import Optional

from loguru import logger
from PyQt6.QtCore import Qt, QThread, QTimer, pyqtSignal  # noqa: F401
from PyQt6.QtWidgets import QApplication  # noqa: F401
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QMainWindow,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import open_containing_folder, safe_open
from filesearch.core.search_engine import FileSearchEngine
from filesearch.models.search_result import SearchResult
from filesearch.plugins.plugin_manager import PluginManager
from filesearch.ui.results_view import ResultsView
from filesearch.ui.search_controls import (
    ProgressWidget,
    SearchControlWidget,
    SearchInputWidget,
    SearchState,
    StatusWidget,
)
from filesearch.ui.sort_controls import SortControls


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

    result_found = pyqtSignal(dict, int)  # result_dict, result_number
    progress_update = pyqtSignal(
        int, str, int
    )  # progress_percent, current_dir, files_found
    search_complete = pyqtSignal(int, int)  # total_files, total_dirs
    error_occurred = pyqtSignal(str, int)  # error_message, error_code
    search_stopped = pyqtSignal(int, int)  # files_found, dirs_searched

    def __init__(
        self,
        search_engine: FileSearchEngine,
        directory: Path,
        query: str,
        progress_callback=None,
    ):
        """Initialize the search worker.

        Args:
            search_engine: FileSearchEngine instance
            directory: Directory to search in
            query: Search pattern
            progress_callback: Callback for progress updates
        """
        super().__init__()
        self.search_engine = search_engine
        self.directory = directory
        self.query = query
        self.progress_callback = progress_callback
        self._is_running = False

        logger.debug(f"SearchWorker initialized for {directory} with query '{query}'")

    def run(self) -> None:
        """Execute the search operation."""
        self._is_running = True
        files_found = 0
        dirs_searched = 0

        try:
            logger.info(f"Starting search in {self.directory} for '{self.query}'")

            # Perform the search (includes plugin results)
            for result in self.search_engine.search(self.directory, self.query):
                if not self._is_running:
                    break

                files_found += 1
                self.result_found.emit(result, files_found)

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

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        plugin_manager: Optional[PluginManager] = None,
    ):
        """Initialize the main window.

        Args:
            config_manager: Configuration manager instance (creates default if None)
            plugin_manager: Plugin manager instance (creates default if None)
        """
        super().__init__()

        # Ensure menu and status bars are created early to prevent
        # None returns during initialization
        self.menuBar()
        self.statusBar()

        # Initialize components
        self.config_manager = config_manager or ConfigManager()
        self.plugin_manager = plugin_manager or PluginManager(self.config_manager)
        self.search_engine = FileSearchEngine(config_manager=self.config_manager)
        self.search_worker: Optional[SearchWorker] = None
        self.is_searching = False
        self.search_results = []
        self.plugin_results = []
        self.current_directory = Path.home()  # Initialize current directory state
        self.search_start_time = 0.0

        # Setup UI
        self.setup_ui()
        self.connect_signals()
        self.load_window_settings()

        # Set focus to search input on launch
        self.query_input.set_focus()

        logger.info("MainWindow initialized")

    def setup_ui(self) -> None:
        """Setup the user interface components."""
        # Set window properties
        self.setWindowTitle("File Search")
        self.setMinimumSize(600, 400)

        # Create menu bar
        menu_bar = self.menuBar()
        if menu_bar is not None:
            settings_menu = menu_bar.addMenu("Settings")
            if settings_menu is not None:
                settings_menu.addAction("Preferences...", self.show_settings_dialog)

        # Create central widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # Create main layout
        main_layout = QVBoxLayout()
        central_widget.setLayout(main_layout)

        # Create search controls layout
        # Search input widget
        self.query_input = SearchInputWidget(self.config_manager)
        main_layout.addWidget(self.query_input)

        # Directory selection widget
        from filesearch.ui.search_controls import DirectorySelectorWidget

        self.directory_selector = DirectorySelectorWidget(self.config_manager)
        self.directory_selector.set_directory(self.current_directory)
        main_layout.addWidget(self.directory_selector)

        # Search control widget
        self.search_control = SearchControlWidget()
        main_layout.addWidget(self.search_control)

        # Progress widget
        self.progress_widget = ProgressWidget()
        main_layout.addWidget(self.progress_widget)

        # Status widget
        self.status_widget = StatusWidget()
        main_layout.addWidget(self.status_widget)

        # Results area
        self.results_label = QLabel("Results:")
        main_layout.addWidget(self.results_label)

        # Sort controls (AC6: UI Controls)
        self.sort_controls = SortControls()
        main_layout.addWidget(self.sort_controls)

        self.results_view = ResultsView()
        main_layout.addWidget(self.results_view)
        # Set ResultsView to occupy 70% of the available space
        main_layout.setStretchFactor(self.results_view, 7)  # 70% of space
        # Set stretch factors for other widgets to occupy remaining 30%
        main_layout.setStretchFactor(self.query_input, 0)  # Fixed size
        main_layout.setStretchFactor(self.directory_selector, 0)  # Fixed size
        main_layout.setStretchFactor(self.search_control, 0)  # Fixed size
        main_layout.setStretchFactor(self.progress_widget, 0)  # Fixed size
        main_layout.setStretchFactor(self.status_widget, 0)  # Fixed size

        # Load and apply highlight settings from config
        self._load_highlight_settings()

        # Load sort settings from config
        self._load_sort_settings()

        # Status bar
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage("Ready")

            # Add time label to status bar
            self.time_label = QLabel()
            status_bar.addPermanentWidget(self.time_label)

            # Add line/column label to status bar
            self.line_col_label = QLabel("Ln 1, Col 1")
            status_bar.addPermanentWidget(self.line_col_label)

        # Timer for updating time
        self.time_update_timer = QTimer()
        self.time_update_timer.timeout.connect(self._update_status_time)
        self.time_update_timer.start(1000)  # Update every second

        logger.debug("UI setup completed")

    def connect_signals(self) -> None:
        """Connect signals and slots for event handling."""
        # Search control widget signals
        self.search_control.search_requested.connect(self.start_search)
        self.search_control.search_stopped.connect(self.stop_search)

        # Search input widget signals
        self.query_input.search_initiated.connect(self.start_search)
        self.query_input.query_empty_changed.connect(
            self.search_control.set_query_empty
        )

        # Directory selector signals
        self.directory_selector.directory_changed.connect(self._on_directory_changed)
        self.directory_selector.enter_pressed.connect(self.start_search)

        # Search engine status signals
        self.search_engine.status_update.connect(self.status_widget.update_status)
        self.search_engine.results_count_update.connect(self._on_results_count_update)

        # Sort controls signals - both save and sort
        self.sort_controls.sortChanged.connect(self.results_view.apply_sorting)
        self.sort_controls.sortChanged.connect(self._on_sort_criteria_changed)

        logger.debug("Signals connected")

    def safe_status_message(self, message: str) -> None:
        """Safely show message on status bar, handling potential None return."""
        status_bar = self.statusBar()
        if status_bar is not None:
            status_bar.showMessage(message)

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

    def _update_status_time(self) -> None:
        """Update the current time display in status bar."""
        current_time = time.strftime("%H:%M:%S")
        self.time_label.setText(current_time)

    def _on_results_count_update(self, increment: int, total: int) -> None:
        """Handle results count update from search engine."""
        self.status_widget.update_status("searching", total)

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

    def _on_sort_criteria_changed(self, criteria) -> None:
        """Handle sort criteria change - save to config"""
        try:
            self.config_manager.set("sorting.criteria", criteria.value)
            self.config_manager.save()
            logger.debug(f"Sort criteria saved: {criteria.value}")
        except Exception as e:
            logger.error(f"Error saving sort criteria: {e}")

    def _on_directory_changed(self, directory: Path) -> None:
        """Update the current search directory state."""
        self.current_directory = directory
        logger.debug(f"Current search directory updated to: {directory}")

    def start_search(self) -> None:
        """Start the file search operation."""
        if self.is_searching:
            logger.warning("Search already in progress")
            return

        # Get search parameters
        directory = self.current_directory
        query = self.query_input.get_text()

        # Validate inputs
        if not directory or not query:
            self.safe_status_message("Please enter both directory and search pattern")
            return

        if not directory.exists():
            self.safe_status_message(f"Directory does not exist: {directory}")
            return

        # Set the query for highlighting (pass to results view)
        self.results_view.set_query(query)

        # Clear previous results
        self.search_results.clear()
        self.results_view.set_searching_state()

        # Record search start time
        self.search_start_time = time.time()

        # Update UI state
        self.is_searching = True
        self.search_control.set_state(SearchState.RUNNING)
        self.query_input.set_loading_state(True)
        self.query_input.set_error_state(False)
        self.directory_selector.set_read_only(True)
        self.setCursor(Qt.CursorShape.WaitCursor)  # Change cursor to wait
        self.safe_status_message(f"Searching in {directory}...")
        logger.info(f"Search started: '{query}' in {directory}")

        # Create and start search worker
        self.search_worker = SearchWorker(self.search_engine, directory, query)

        # Connect search worker signals to slots
        self.search_worker.result_found.connect(self.on_result_found)
        self.search_worker.progress_update.connect(self.on_progress_update)
        self.search_worker.search_complete.connect(self.on_search_complete)
        self.search_worker.error_occurred.connect(self.on_search_error)
        self.search_worker.search_stopped.connect(self.on_search_stopped)

        # Start the search in background thread
        self.search_worker.start()

    def stop_search(self) -> None:
        """Stop the current search operation."""
        if not self.is_searching or not self.search_worker:
            return

        self.search_worker.stop()
        self.safe_status_message("Stopping search...")
        logger.info("Search stop requested")

    def on_result_found(self, result: dict, result_number: int) -> None:
        """Handle search result found signal.

        Args:
            result: Result dictionary
            result_number: Result number
        """
        self.search_results.append(result)

        # Create SearchResult and add to results view
        search_result = SearchResult(
            path=Path(result["path"]),
            size=result["size"],
            modified=result["modified"],
            plugin_source=result.get("source"),
        )
        self.results_view.add_result(search_result)

        # Update status periodically
        if result_number % 10 == 0:
            self.safe_status_message(f"Found {result_number} files...")

        logger.debug(f"Result found: {result} (#{result_number})")

    def on_progress_update(
        self, progress: int, current_dir: str, files_found: int
    ) -> None:
        """Handle progress update signal.

        Args:
            progress: Progress percentage
            current_dir: Current directory being searched
            files_found: Number of files found so far
        """
        self.safe_status_message(
            f"Searching {current_dir}... Found {files_found} files"
        )
        logger.debug(f"Progress: {progress}% in {current_dir}, {files_found} files")

    def on_search_complete(self, total_files: int, total_dirs: int) -> None:
        """Handle search complete signal.

        Args:
            total_files: Total files found
            total_dirs: Total directories searched
        """
        duration = time.time() - self.search_start_time
        self.progress_widget.set_completed_state(total_files)
        self.progress_widget.hide_progress()
        self.reset_search_ui()
        self.status_widget.update_status(
            "completed",
            total_files,
            query=self.query_input.get_text(),
            directory=str(self.current_directory),
            duration=duration,
        )
        self.safe_status_message(
            "Found {} results in {:.1f}s".format(total_files, duration)
        )
        # Auto-scroll to first result when search completes
        if (
            hasattr(self.results_view, "_results_model")
            and self.results_view._results_model
            and self.results_view._results_model.rowCount() > 0
        ):
            self.results_view.scrollTo(self.results_view._results_model.index(0, 0))
        logger.info(
            f"Search completed: {total_files} files in {total_dirs} directories"
        )

    def on_search_stopped(self, files_found: int, dirs_searched: int) -> None:
        """Handle search stopped signal.

        Args:
            files_found: Files found before stopping
            dirs_searched: Directories searched before stopping
        """
        duration = time.time() - self.search_start_time
        self.progress_widget.hide_progress()
        self.reset_search_ui()
        self.status_widget.update_status(
            "completed",
            files_found,
            query=self.query_input.get_text(),
            directory=str(self.current_directory),
            duration=duration,
        )
        self.safe_status_message(f"Search stopped: {files_found} files found")
        logger.info(
            f"Search stopped: {files_found} files in {dirs_searched} directories"
        )

    def on_search_error(self, error_message: str, error_code: int) -> None:
        """Handle search error signal.

        Args:
            error_message: Error message
            error_code: Error code
        """
        self.progress_widget.set_error_state(error_message)
        self.progress_widget.hide_progress()
        self.reset_search_ui()
        self.query_input.set_error_state(True)
        self.status_widget.set_error_message(error_message)
        self.safe_status_message(f"Error: {error_message}")
        logger.error(f"Search error {error_code}: {error_message}")

    def reset_search_ui(self) -> None:
        """Reset UI to ready state after search completes."""
        self.is_searching = False
        self.search_control.set_state(SearchState.IDLE)
        self.query_input.set_loading_state(False)
        self.directory_selector.set_read_only(False)
        self.setCursor(Qt.CursorShape.ArrowCursor)  # Reset cursor to normal

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
            self.safe_status_message(f"Opened: {file_path.name}")
            logger.info(f"Opened file: {file_path}")
        except FileSearchError as e:
            self.safe_status_message(f"Error opening file: {e}")
            logger.error(f"Error opening file {file_path}: {e}")

    def open_selected_folder(self, file_path: Path) -> None:
        """Open the containing folder of selected file.

        Args:
            file_path: Path to the file
        """
        try:
            open_containing_folder(file_path)
            self.safe_status_message(f"Opened folder: {file_path.parent}")
            logger.info(f"Opened folder: {file_path.parent}")
        except FileSearchError as e:
            self.safe_status_message(f"Error opening folder: {e}")
            logger.error(f"Error opening folder for {file_path}: {e}")

    def _load_highlight_settings(self) -> None:
        """Load highlighting settings from config and apply to results view."""
        try:
            # Load highlight settings from config
            highlight_enabled = self.config_manager.get("highlighting.enabled", True)
            highlight_color = self.config_manager.get("highlighting.color", "#FFFF99")
            highlight_style = self.config_manager.get(
                "highlighting.style", "background"
            )

            # Apply to results view
            self.results_view.set_highlight_enabled(highlight_enabled)
            self.results_view.set_highlight_color(highlight_color)
            self.results_view.set_highlight_style(highlight_style)

            logger.debug(
                f"Highlight settings loaded: enabled={highlight_enabled}, "
                f"color={highlight_color}, style={highlight_style}"
            )

        except Exception as e:
            logger.error(f"Error loading highlight settings: {e}")

    def _load_sort_settings(self) -> None:
        """Load sort settings from config and apply"""
        try:
            from ..core.sort_engine import SortCriteria

            # Load saved sort criteria
            criteria_str = self.config_manager.get("sorting.criteria", "name_asc")

            # Map string to SortCriteria
            criteria_map = {
                "name_asc": SortCriteria.NAME_ASC,
                "name_desc": SortCriteria.NAME_DESC,
                "size_asc": SortCriteria.SIZE_ASC,
                "size_desc": SortCriteria.SIZE_DESC,
                "date_asc": SortCriteria.DATE_ASC,
                "date_desc": SortCriteria.DATE_DESC,
                "type_asc": SortCriteria.TYPE_ASC,
                "relevance_desc": SortCriteria.RELEVANCE_DESC,
            }

            criteria = criteria_map.get(criteria_str, SortCriteria.NAME_ASC)

            # Apply to sort controls
            self.sort_controls.set_criteria(criteria)

            logger.debug(f"Sort settings loaded: criteria={criteria_str}")

        except Exception as e:
            logger.error(f"Error loading sort settings: {e}")

    def show_settings_dialog(self) -> None:
        """Show the settings dialog."""
        try:
            from filesearch.ui.settings_dialog import SettingsDialog

            dialog = SettingsDialog(self.config_manager, self.plugin_manager, self)
            dialog.exec()
            logger.info("Settings dialog shown")
        except Exception as e:
            self.safe_status_message(f"Error opening settings: {e}")
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
