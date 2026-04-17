"""Main GUI window module for the file search application.

This module provides the MainWindow class that implements the main user interface
with search input, directory selection, and results display functionality.
"""

import time
from pathlib import Path
from typing import List, Optional

from loguru import logger
from PyQt6.QtCore import (  # noqa: F401
    QKeyCombination,
    QPoint,
    Qt,
    QThread,
    QTimer,
    pyqtSignal,
)
from PyQt6.QtGui import (  # noqa: F401
    QAction,
    QKeySequence,
)
from PyQt6.QtWidgets import (  # noqa: F401
    QApplication,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QSplitter,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import FileSearchError
from filesearch.core.file_utils import (
    normalize_path,
    open_containing_folder,
    safe_open,
    validate_directory,
)
from filesearch.core.search_engine import FileSearchEngine
from filesearch.models.search_result import SearchResult
from filesearch.plugins.plugin_manager import PluginManager
from filesearch.ui.context_menu_handler import ContextMenuHandlerMixin
from filesearch.ui.details_panel import DetailsPanelWidget
from filesearch.ui.results_view import ResultsView
from filesearch.ui.search_controls import (
    ProgressWidget,
    SearchControlWidget,
    SearchInputWidget,
    SearchState,
    StatusWidget,
)
from filesearch.ui.search_worker import SearchWorker  # noqa: F401 — re-exported
from filesearch.ui.settings_dialog import SettingsDialog
from filesearch.ui.sidebar_widget import SidebarWidget
from filesearch.ui.sort_controls import SortControls


class MainWindow(ContextMenuHandlerMixin, QMainWindow):
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
        self.current_directory = self._get_startup_directory()
        self.search_start_time = 0.0

        # Setup UI
        self.setup_ui()
        self.connect_signals()
        self.load_window_settings()

        # Set focus to search input on launch
        self.query_input.set_focus()

        # Setup context menu actions
        self._setup_context_menu()

        logger.info("MainWindow initialized")

    def setup_ui(self) -> None:
        """Setup the user interface with 3-panel QSplitter layout."""
        # Set window properties
        self.setWindowTitle("File Search")
        self.setMinimumSize(900, 550)

        # Create menu bar
        menu_bar = self.menuBar()
        if menu_bar is not None:
            settings_menu = menu_bar.addMenu("Settings")
            if settings_menu is not None:
                settings_menu.addAction("Preferences...", self.show_settings_dialog)

        # Create central widget with a thin wrapper layout
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        wrapper = QVBoxLayout(central_widget)
        wrapper.setContentsMargins(0, 0, 0, 0)
        wrapper.setSpacing(0)

        # ---- Main horizontal splitter: Sidebar | Center | Details ----
        self.main_splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- 1. Sidebar ---
        self.sidebar = SidebarWidget()
        self.main_splitter.addWidget(self.sidebar)

        # --- 2. Center panel ---
        center_panel = QWidget()
        center_panel.setObjectName("centerPanel")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setContentsMargins(16, 12, 16, 8)
        center_layout.setSpacing(10)

        # Search input widget (redesigned search bar)
        self.query_input = SearchInputWidget(self.config_manager)
        center_layout.addWidget(self.query_input)

        # Directory selector (hidden — sidebar provides this)
        from filesearch.ui.search_controls import DirectorySelectorWidget

        self.directory_selector = DirectorySelectorWidget(self.config_manager)
        self.directory_selector.set_directory(self.current_directory)
        self.directory_selector.setVisible(False)
        center_layout.addWidget(self.directory_selector)

        # Search control widget (hidden — search triggered by Enter / auto-search)
        self.search_control = SearchControlWidget()
        self.search_control.setVisible(False)
        center_layout.addWidget(self.search_control)

        # Progress widget
        self.progress_widget = ProgressWidget()
        center_layout.addWidget(self.progress_widget)

        # Status widget
        self.status_widget = StatusWidget()
        center_layout.addWidget(self.status_widget)

        # Results header + sort controls in one row
        results_header = QHBoxLayout()
        results_header.setSpacing(8)
        self.results_label = QLabel("RESULTS")
        self.results_label.setProperty("class", "results-header")
        results_header.addWidget(self.results_label)

        self.sort_controls = SortControls()
        results_header.addWidget(self.sort_controls)
        results_header.addStretch()
        center_layout.addLayout(results_header)

        # Results view
        self.results_view = ResultsView()
        center_layout.addWidget(self.results_view, 1)

        self.main_splitter.addWidget(center_panel)

        # --- 3. Details panel (hidden by default) ---
        self.details_panel = DetailsPanelWidget()
        self.main_splitter.addWidget(self.details_panel)

        # Splitter sizes — sidebar 240, center stretch, details 0 (hidden)
        self.main_splitter.setSizes([240, 600, 0])
        self.main_splitter.setStretchFactor(0, 0)  # sidebar fixed
        self.main_splitter.setStretchFactor(1, 1)  # center stretches
        self.main_splitter.setStretchFactor(2, 0)  # details fixed
        # Allow details panel (index 2) to collapse to 0
        self.main_splitter.setCollapsible(0, False)
        self.main_splitter.setCollapsible(1, False)
        self.main_splitter.setCollapsible(2, True)

        wrapper.addWidget(self.main_splitter)

        # Load and apply highlight settings from config
        self._load_highlight_settings()

        # Load sort settings from config
        self._load_sort_settings()

        # Update sidebar tags from search history
        self._update_sidebar_tags()
        self._refresh_custom_sidebar_location()
        self.sidebar.set_active_location_by_path(self.current_directory)

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

        # Results view signals
        self.results_view.file_open_requested.connect(self._on_file_open_requested)
        self.results_view.folder_open_requested.connect(
            lambda r: self.open_selected_folder(r.path)
        )
        # Context menu request signal from ResultsView
        self.results_view.context_menu_requested.connect(
            self._on_context_menu_requested
        )

        # --- Sidebar signals ---
        self.sidebar.directory_selected.connect(self._on_sidebar_directory_selected)
        self.sidebar.browse_requested.connect(self._browse_for_search_directory)
        self.sidebar.file_type_filter_changed.connect(
            self._on_file_type_filter_changed
        )
        self.sidebar.tag_clicked.connect(self._on_tag_clicked)

        # --- Details panel signals ---
        self.details_panel.open_requested.connect(self._on_file_open_requested)
        self.details_panel.open_folder_requested.connect(
            lambda r: self.open_selected_folder(r.path)
        )
        self.details_panel.copy_path_requested.connect(
            lambda r: self._handle_context_copy_path([r])
        )
        self.details_panel.delete_requested.connect(
            lambda r: self._handle_context_delete([r])
        )
        self.details_panel.panel_close_requested.connect(
            self._on_details_panel_close
        )

        # --- Result selection → details panel ---
        self.results_view.clicked.connect(self._on_result_selection_changed)

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

    # --- Sidebar / details panel handlers ---

    def _on_file_type_filter_changed(self, extensions: list) -> None:
        """Handle sidebar file-type filter toggle — filter results client-side."""
        model = self.results_view._results_model
        if model and hasattr(model, "set_extension_filter"):
            model.set_extension_filter(extensions)
        logger.debug(f"File type filter: {extensions or 'all'}")

    def _on_tag_clicked(self, text: str) -> None:
        """Handle sidebar tag click — set search text and start search."""
        self.query_input.set_text(text)
        self.start_search()
        logger.debug(f"Tag clicked: {text}")

    def _on_result_selection_changed(self, index) -> None:
        """Handle result list selection — show details panel."""
        if not index.isValid():
            return
        result = index.data(Qt.ItemDataRole.UserRole)
        if result is not None:
            self.details_panel.show_result(result)
            # Ensure splitter gives the details panel width
            sizes = self.main_splitter.sizes()
            if sizes[2] < 10:
                # Steal space from center panel to open details
                details_w = 280
                center_w = max(300, sizes[1] - details_w)
                self.main_splitter.setSizes([sizes[0], center_w, details_w])

    def _on_details_panel_close(self) -> None:
        """Hide the details panel and reclaim space."""
        self.details_panel.clear()
        # Give the details panel's space back to center
        sizes = self.main_splitter.sizes()
        self.main_splitter.setSizes([sizes[0], sizes[1] + sizes[2], 0])

    def _update_sidebar_tags(self) -> None:
        """Load recent searches into sidebar tags."""
        try:
            searches = self.config_manager.get("recent.searches", [])
            self.sidebar.set_tags(searches)
        except Exception as e:
            logger.warning(f"Could not load sidebar tags: {e}")

    def show_settings_dialog(self) -> None:
        """Show the settings dialog."""
        dialog = SettingsDialog(self.config_manager, self.plugin_manager, self)
        if dialog.exec():
            # Settings were saved, reload any affected components
            self._load_highlight_settings()
            self._load_sort_settings()
            logger.info("Settings dialog closed with changes saved")
        else:
            logger.debug("Settings dialog cancelled")

    def _load_highlight_settings(self) -> None:
        """Load and apply highlight settings from configuration."""
        try:
            # Load highlight settings if the results view supports it
            if hasattr(self.results_view, "set_highlight_enabled"):
                enabled = self.config_manager.get("highlighting.enabled", True)
                self.results_view.set_highlight_enabled(enabled)

                color = self.config_manager.get("highlighting.color", "#FFFF99")
                if hasattr(self.results_view, "set_highlight_color"):
                    self.results_view.set_highlight_color(color)

                case_sensitive = self.config_manager.get(
                    "highlighting.case_sensitive", False
                )
                if hasattr(self.results_view, "set_highlight_case_sensitive"):
                    self.results_view.set_highlight_case_sensitive(case_sensitive)

                logger.debug("Highlight settings loaded")
        except Exception as e:
            logger.error(f"Error loading highlight settings: {e}")

    def _load_sort_settings(self) -> None:
        """Load and apply sort settings from configuration."""
        try:
            # Load sort criteria from config
            from filesearch.core.sort_engine import SortCriteria

            criteria_str = self.config_manager.get("sorting.criteria", "name_asc")

            # Convert string to SortCriteria enum
            criteria = SortCriteria(criteria_str)

            # Apply to sort controls
            if hasattr(self.sort_controls, "set_criteria"):
                self.sort_controls.set_criteria(criteria)

            logger.debug(f"Sort settings loaded: {criteria_str}")
        except Exception as e:
            logger.error(f"Error loading sort settings: {e}")

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

    def _get_startup_directory(self) -> Path:
        """Resolve the initial search directory from config, falling back to home."""
        configured_directory = self.config_manager.get(
            "search_preferences.default_search_directory",
            str(Path.home()),
        )

        try:
            directory = normalize_path(str(configured_directory))
            if validate_directory(directory) is None:
                return directory
        except Exception as e:
            logger.warning(
                f"Invalid configured default search directory '{configured_directory}': {e}"
            )

        return Path.home()

    def _set_search_directory(
        self, directory: Path, persist: bool = False, update_recent: bool = False
    ) -> None:
        """Synchronize the active search directory across UI and configuration."""
        self.current_directory = directory
        self.directory_selector.set_directory(directory)

        if update_recent:
            self.directory_selector.remember_directory(directory)
            self._refresh_custom_sidebar_location()

        self.sidebar.set_active_location_by_path(directory)

        if persist:
            self.config_manager.set(
                "search_preferences.default_search_directory", str(directory)
            )
            self.config_manager.save()

    def _refresh_custom_sidebar_location(self) -> None:
        """Show the most recent custom folder in the sidebar, when available."""
        home = Path.home()
        preset_paths = {
            home,
            home / "Documents",
            home / "Desktop",
            home / "Downloads",
            home / "Pictures",
            home / "Videos",
        }
        recent_directories = self.config_manager.get("recent.directories", [])

        custom_path: Optional[Path] = None
        for directory in recent_directories:
            candidate = Path(directory)
            if candidate in preset_paths:
                continue
            if validate_directory(candidate) is None:
                custom_path = candidate
                break

        if (
            custom_path is None
            and self.current_directory not in preset_paths
            and validate_directory(self.current_directory) is None
        ):
            custom_path = self.current_directory

        self.sidebar.set_custom_location(custom_path)

    def _browse_for_search_directory(self) -> None:
        """Open a folder picker and make the selection the active search root."""
        initial_dir = self.current_directory
        if validate_directory(initial_dir):
            initial_dir = self._get_startup_directory()

        selected_dir = QFileDialog.getExistingDirectory(
            self,
            "Select Search Directory",
            str(initial_dir),
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )

        if not selected_dir:
            logger.debug("Sidebar browse cancelled")
            return

        selected_path = Path(selected_dir)
        self._set_search_directory(selected_path, persist=True, update_recent=True)
        self.safe_status_message(f"Search folder selected: {selected_path}")
        logger.info(f"Search directory selected from sidebar: {selected_path}")

    def _on_sidebar_directory_selected(self, directory: Path) -> None:
        """Handle sidebar location click and update the active search directory."""
        self._set_search_directory(directory, persist=True, update_recent=False)
        logger.debug(f"Sidebar directory selected: {directory}")

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

        # Refresh sidebar tags with latest search history
        self._update_sidebar_tags()

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
        # Show wait cursor
        QApplication.setOverrideCursor(Qt.CursorShape.WaitCursor)
        try:
            open_containing_folder(file_path)
            self.safe_status_message(f"Opened folder: {file_path.parent}")
            logger.info(f"Opened folder: {file_path.parent}")
        except FileSearchError as e:
            self.safe_status_message(f"Error opening folder: {e}")
            logger.error(f"Error opening folder for {file_path}: {e}")
            # Show error dialog
            QMessageBox.critical(
                self, "Error", f"Failed to open containing folder: \n{e}"
            )
        finally:
            # Restore cursor
            QApplication.restoreOverrideCursor()

    def _on_file_open_requested(self, search_result: SearchResult) -> None:
        """Handle file opening request from results view.

        Args:
            search_result: SearchResult object for the file to open
        """
        try:
            # Get security manager for executable warnings
            from filesearch.core.security_manager import get_security_manager

            security_manager = get_security_manager(self.config_manager)

            # Check if file is executable and should warn
            should_warn, warning_message = security_manager.should_warn_before_opening(
                search_result.path
            )

            if should_warn:
                # Show warning dialog
                from PyQt6.QtCore import Qt
                from PyQt6.QtWidgets import QCheckBox, QMessageBox

                msg_box = QMessageBox()
                msg_box.setIcon(QMessageBox.Icon.Warning)
                msg_box.setWindowTitle("Security Warning")
                msg_box.setText(warning_message)

                # Add checkbox for "Always allow" option
                checkbox = QCheckBox("Always open files of this type")
                checkbox.setChecked(False)
                msg_box.setCheckBox(checkbox)

                msg_box.setStandardButtons(
                    QMessageBox.StandardButton.Open | QMessageBox.StandardButton.Cancel
                )
                msg_box.setDefaultButton(QMessageBox.StandardButton.Cancel)

                result = msg_box.exec()

                if result == QMessageBox.StandardButton.Open:
                    # User chose to open
                    if checkbox.isChecked():
                        # Remember user preference
                        security_manager.allow_extension(search_result.path.suffix)

                    self._open_file_with_status(search_result.path)
                else:
                    # User cancelled
                    self.safe_status_message("File opening cancelled")
                    logger.info(
                        f"User cancelled opening executable file: {search_result.path}"
                    )
            else:
                # No warning needed, open directly
                self._open_file_with_status(search_result.path)

        except Exception as e:
            self.safe_status_message(f"Error checking file security: {e}")
            logger.error(f"Error checking file security for {search_result.path}: {e}")

    def _open_file_with_status(self, file_path: Path) -> None:
        """Open file with status bar updates.

        Args:
            file_path: Path to the file to open
        """
        try:
            # Show opening status
            self.safe_status_message(f"Opening: {file_path.name}...")

            # Import safe_open here to avoid circular imports
            from filesearch.core.file_utils import safe_open

            safe_open(file_path)

            # Show success status
            self.safe_status_message(f"Opened: {file_path.name}")
            logger.info(f"Successfully opened file: {file_path}")

            # Add to recently opened files
            self.config_manager.add_recent_file(file_path)

        except FileSearchError as e:
            # Handle specific error types
            error_msg = str(e)

            if "SECURITY_WARNING:" in error_msg:
                # This shouldn't happen here as we handle warnings above
                return
            elif "does not exist" in error_msg.lower():
                self.safe_status_message(f"File no longer exists: {file_path.name}")
            elif "permission denied" in error_msg.lower():
                self.safe_status_message(f"Permission denied: {file_path.name}")
            elif "no application" in error_msg.lower():
                self.safe_status_message(
                    f"No application associated with this file type: {file_path.suffix}"
                )
            else:
                self.safe_status_message(f"Failed to open: {file_path.name}")

            logger.error(f"Error opening file {file_path}: {e}")

            # Offer to open containing folder as fallback
            from PyQt6.QtWidgets import QMessageBox

            reply = QMessageBox.question(
                self,
                "Open Containing Folder",
                f"Could not open {file_path.name}. Would you like to open its "
                f"containing folder instead?",
                QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
                QMessageBox.StandardButton.Yes,
            )

            if reply == QMessageBox.StandardButton.Yes:
                self.open_selected_folder(file_path)

    def closeEvent(self, event) -> None:
        """Handle window close event."""
        self.save_window_settings()
        if self.search_worker:
            self.search_worker.stop()
            self.search_worker.wait()
        super().closeEvent(event)


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
