"""Search controls module for file search application.

This module provides SearchInputWidget class that implements an advanced search
input field with history, auto-complete, visual feedback, and comprehensive
keyboard support.
"""

import locale
import os
import time
from enum import Enum
from pathlib import Path
from typing import List, Optional

from loguru import logger
from PyQt6.QtCore import QEvent, QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QDropEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QApplication,
    QCompleter,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QProgressBar,
    QPushButton,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import SearchError
from filesearch.core.file_utils import normalize_path, validate_directory


class SearchState(Enum):
    """Enumeration of possible search control states."""

    IDLE = "idle"
    RUNNING = "running"
    STOPPING = "stopping"
    COMPLETED = "completed"
    ERROR = "error"


class SearchInputWidget(QWidget):
    """Advanced search input widget with history and visual feedback.

    This widget provides a search input field with comprehensive features including
    search history, auto-complete, visual feedback states, and full keyboard
    accessibility support.

    Signals:
        search_initiated(str): Emitted when user initiates a search
        text_changed(str): Emitted when search text changes
        escape_pressed(): Emitted when escape key is pressed
        focus_gained(): Emitted when widget gains focus
        focus_lost(): Emitted when widget loses focus
    """

    # Signals
    search_initiated = pyqtSignal(str)
    text_changed = pyqtSignal(str)
    escape_pressed = pyqtSignal()
    focus_gained = pyqtSignal()
    focus_lost = pyqtSignal()
    query_empty_changed = pyqtSignal(bool)

    # Constants for styling and behavior
    MAX_SEARCH_LENGTH = 255
    SEARCH_HISTORY_SIZE = 10
    DEFAULT_AUTO_SEARCH_DELAY_MS = 500

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        parent: Optional[QWidget] = None,
    ):
        """Initialize search input widget.

        Args:
            config_manager: Configuration manager for search history persistence
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Configuration
        self.config_manager = config_manager
        self.search_history: List[str] = []
        self.is_loading = False
        self.has_error = False

        # Auto-search configuration
        self.auto_search_enabled = True
        self.auto_search_delay_ms = self.DEFAULT_AUTO_SEARCH_DELAY_MS

        # Debounce timer for auto-search
        self._debounce_timer = QTimer()
        self._debounce_timer.setSingleShot(True)
        self._debounce_timer.timeout.connect(self._on_debounce_timeout)

        # Setup UI
        self._setup_ui()
        self._setup_style()
        self._load_search_history()
        self._load_auto_search_config()

        logger.debug("SearchInputWidget initialized")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Label
        self.label = QLabel("Search files and folders")
        self.label.setProperty("class", "search-label")
        layout.addWidget(self.label)

        # Create a container for the search input with clear button and loading indicator
        search_container = QWidget()
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(0, 0, 0, 0)
        search_layout.setSpacing(0)
        search_container.setLayout(search_layout)

        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Enter filename or partial name...")
        self.search_input.setMaxLength(self.MAX_SEARCH_LENGTH)
        self.search_input.setProperty("class", "search-input")
        self.search_input.setMaximumWidth(900)  # Prevent expanding to window edge

        # Set accessibility attributes
        self.search_input.setAccessibleName("Search input")
        self.search_input.setAccessibleDescription(
            "Enter filename or partial name to search for files and folders"
        )

        # Set text alignment to ensure proper vertical centering
        self.search_input.setAlignment(Qt.AlignmentFlag.AlignVCenter)

        # Clear button
        self.clear_button = QToolButton()
        self.clear_button.setText("✕")
        self.clear_button.setProperty("class", "clear-button")
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setVisible(False)  # Hidden by default
        self.clear_button.clicked.connect(self.clear_text)
        self.clear_button.setFixedSize(24, 24)

        # Loading indicator (simple text for now, can be replaced with spinner)
        self.loading_indicator = QLabel("⟳")
        self.loading_indicator.setProperty("class", "loading-indicator")
        self.loading_indicator.setVisible(False)
        self.loading_indicator.setFixedSize(24, 24)

        # Add widgets to search container
        search_layout.addWidget(self.search_input)
        search_layout.addWidget(self.clear_button)
        search_layout.addWidget(self.loading_indicator)

        # Add search container to main layout
        layout.addWidget(search_container)

        # Set widget size policy for proper sizing
        self.setMinimumWidth(400)  # Minimum 400px as per AC
        self.setMaximumWidth(1200)  # Prevent excessive expansion

        # Connect signals
        self.connect_signals()

        logger.debug("UI setup completed")

    def _setup_style(self) -> None:
        """Setup widget styling."""
        # Base style for widget
        self.setStyleSheet(
            """
            QWidget#searchInputWidget {
                background: transparent;
            }

            QLabel.search-label {
                font-size: 12px;
                font-weight: bold;
                color: #666666;
                margin-bottom: 4px;
            }

            QLineEdit.search-input {
                font-size: 13px;
                padding: 12px;
                border: 2px solid #cccccc;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.95);
                color: #000000;
                selection-background-color: #0078d4;
            }

            QLineEdit.search-input:focus {
                border-color: #0078d4;
                outline: none;
            }

            QLineEdit.search-input[state="error"] {
                border-color: #d13438;
            }

            QToolButton.clear-button {
                border: none;
                background: transparent;
                color: #666666;
                font-size: 16px;
                padding: 4px;
                margin-right: 8px;
            }

            QToolButton.clear-button:hover {
                color: #333333;
                background: rgba(0, 0, 0, 0.1);
                border-radius: 2px;
            }

            QLabel.loading-indicator {
                color: #0078d4;
                font-size: 16px;
                padding: 4px;
            }
        """
        )

        # Set object name for styling
        self.setObjectName("searchInputWidget")

        logger.debug("Styling setup completed")

    def _load_search_history(self) -> None:
        """Load search history from configuration."""
        if not self.config_manager:
            return

        try:
            self.search_history = self.config_manager.get("recent.searches", [])
            # Ensure we don't exceed the maximum
            self.search_history = self.search_history[: self.SEARCH_HISTORY_SIZE]

            # Setup completer with search history
            self._setup_completer()

            logger.debug(f"Loaded {len(self.search_history)} search history items")

        except Exception as e:
            logger.error(f"Error loading search history: {e}")
            self.search_history = []

    def _setup_completer(self) -> None:
        """Setup auto-completer with search history."""
        if not self.search_history:
            return

        completer = QCompleter(self.search_history)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self.search_input.setCompleter(completer)

        logger.debug("Auto-completer setup completed")

    def _load_auto_search_config(self) -> None:
        """Load auto-search configuration."""
        if not self.config_manager:
            return

        try:
            self.auto_search_enabled = self.config_manager.get(
                "search.auto_search_enabled", True
            )
            self.auto_search_delay_ms = self.config_manager.get(
                "search.auto_search_delay_ms", self.DEFAULT_AUTO_SEARCH_DELAY_MS
            )
            logger.debug(
                f"Auto-search config loaded: enabled={self.auto_search_enabled}, "
                f"delay={self.auto_search_delay_ms}ms"
            )
        except Exception as e:
            logger.error(f"Error loading auto-search config: {e}")
            self.auto_search_enabled = True
            self.auto_search_delay_ms = self.DEFAULT_AUTO_SEARCH_DELAY_MS

    def _save_search_history(self) -> None:
        """Save search history to configuration."""
        if not self.config_manager:
            return

        try:
            self.config_manager.set("recent.searches", self.search_history)
            self.config_manager.save()
            logger.debug("Search history saved")

        except Exception as e:
            logger.error(f"Error saving search history: {e}")

    def _add_to_search_history(self, query: str) -> None:
        """Add query to search history.

        Args:
            query: Search query to add to history
        """
        if not query or not query.strip():
            return

        query = query.strip()

        # Remove if already exists
        if query in self.search_history:
            self.search_history.remove(query)

        # Add to beginning
        self.search_history.insert(0, query)

        # Trim to maximum size
        self.search_history = self.search_history[: self.SEARCH_HISTORY_SIZE]

        # Update completer
        self._setup_completer()

        # Save to configuration
        self._save_search_history()

        logger.debug(f"Added to search history: '{query}'")

    def set_loading_state(self, is_loading: bool) -> None:
        """Set loading state of the search input.

        Args:
            is_loading: Whether to show loading indicator
        """
        self.is_loading = is_loading
        self.loading_indicator.setVisible(is_loading)

        # Update style based on state
        if is_loading:
            self.search_input.setProperty("state", "loading")
        else:
            self.search_input.setProperty("state", "normal")

        # Apply style changes
        style = self.search_input.style()
        if style:
            style.unpolish(self.search_input)
            style.polish(self.search_input)

        logger.debug(f"Loading state set to: {is_loading}")

    def set_error_state(self, has_error: bool) -> None:
        """Set error state of the search input.

        Args:
            has_error: Whether to show error state
        """
        self.has_error = has_error

        # Update style based on state
        if has_error:
            self.search_input.setProperty("state", "error")
        else:
            self.search_input.setProperty("state", "normal")

        # Apply style changes
        style = self.search_input.style()
        if style:
            style.unpolish(self.search_input)
            style.polish(self.search_input)

        logger.debug(f"Error state set to: {has_error}")

    def clear_text(self) -> None:
        """Clear search input text."""
        self.search_input.clear()
        self.clear_button.setVisible(False)
        self.text_changed.emit("")
        self.query_empty_changed.emit(True)
        logger.debug("Search input cleared")

    def get_text(self) -> str:
        """Get current search text.

        Returns:
            Current search text
        """
        return self.search_input.text().strip()

    def set_text(self, text: str) -> None:
        """Set search text.

        Args:
            text: Text to set in the search input
        """
        self.search_input.setText(text)
        self._update_clear_button_visibility()
        self.text_changed.emit(text)
        self.query_empty_changed.emit(not bool(text.strip()))

    def set_focus(self) -> None:
        """Set focus to the search input."""
        self.search_input.setFocus()
        self.search_input.selectAll()
        logger.debug("Focus set to search input")

    def _update_clear_button_visibility(self) -> None:
        """Update clear button visibility based on text content."""
        has_text = bool(self.search_input.text().strip())
        self.clear_button.setVisible(has_text and not self.is_loading)

    def _on_debounce_timeout(self) -> None:
        """Handle debounce timer timeout for auto-search."""
        query = self.get_text()
        if query:
            self.search_initiated.emit(query)
            logger.debug(f"Auto-search initiated for: '{query}'")

    def keyPressEvent(self, a0) -> None:
        """Handle key press events.

        Args:
            a0: Key event
        """
        event = a0

        # Handle special key combinations
        if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
            # Enter key initiates search
            query = self.get_text()
            if query:
                self._add_to_search_history(query)
                self.search_initiated.emit(query)
                logger.debug(f"Search initiated via Enter key: '{query}'")
            return

        elif event.key() == Qt.Key.Key_Escape:
            # Escape key clears input and returns focus
            self.clear_text()
            self.escape_pressed.emit()
            logger.debug("Escape key pressed - input cleared")
            return

        elif (
            event.key() == Qt.Key.Key_L
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            # Ctrl+L selects all text
            self.search_input.selectAll()
            logger.debug("Ctrl+L pressed - text selected")
            return

        elif event.key() == Qt.Key.Key_Down:
            # Down arrow shows completer
            completer = self.search_input.completer()
            if completer and self.search_history:
                completer.complete()
                logger.debug("Down arrow pressed - showing completer")
                return

        # Let parent handle other keys
        super().keyPressEvent(a0)

    def focusInEvent(self, a0) -> None:
        """Handle focus in event.

        Args:
            a0: Focus event
        """
        super().focusInEvent(a0)
        self.focus_gained.emit()
        logger.debug("Search input gained focus")

    def focusOutEvent(self, a0) -> None:
        """Handle focus out event.

        Args:
            a0: Focus event
        """
        super().focusOutEvent(a0)
        self.focus_lost.emit()
        logger.debug("Search input lost focus")

    def connect_signals(self) -> None:
        """Connect signals and slots for the search input."""
        # Text changed signal (with debouncing for auto-search)
        self.search_input.textChanged.connect(self._on_text_changed)

        # Clear button visibility
        self.search_input.textChanged.connect(self._update_clear_button_visibility)

        logger.debug("Signals connected")

    def _on_text_changed(self, text: str) -> None:
        """Handle text change events.

        Args:
            text: New text content
        """
        # Emit text changed signal
        self.text_changed.emit(text)

        # Emit query empty state
        is_empty = not bool(text.strip())
        self.query_empty_changed.emit(is_empty)

        # Restart debounce timer for auto-search
        self._debounce_timer.stop()
        if self.auto_search_enabled and text.strip():
            self._debounce_timer.start(self.auto_search_delay_ms)


class DirectorySelectorWidget(QWidget):
    """Widget for selecting the search directory with a text input and browse button.

    Signals:
        directory_changed(Path): Emitted when the directory path is updated.
        browse_clicked(): Emitted when the browse button is clicked.
        enter_pressed(): Emitted when Enter key is pressed in directory input.
    """

    directory_changed = pyqtSignal(Path)
    browse_clicked = pyqtSignal()
    enter_pressed = pyqtSignal()

    def __init__(
        self,
        config_manager: Optional[ConfigManager] = None,
        parent: Optional[QWidget] = None,
    ):
        super().__init__(parent)
        self.config_manager = config_manager
        self.recent_directories: List[str] = []
        self._setup_ui()
        self._setup_style()
        self._load_recent_directories()
        self._set_default_directory()
        self._setup_completer()

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Main layout for the widget
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Label
        self.label = QLabel("Search Directory")
        self.label.setProperty("class", "directory-label")
        layout.addWidget(self.label)

        # Horizontal container for input and button
        h_layout_widget = QWidget()
        h_layout = QHBoxLayout()
        h_layout.setContentsMargins(0, 0, 0, 0)
        h_layout.setSpacing(4)
        h_layout_widget.setLayout(h_layout)

        # Directory input field
        self.directory_input = QLineEdit()
        self.directory_input.setPlaceholderText("Enter directory path or browse...")
        self.directory_input.setProperty("class", "directory-input")
        self.directory_input.setMinimumHeight(32)
        h_layout.addWidget(self.directory_input)

        # Dropdown button for recent directories
        self.recent_button = QToolButton()
        self.recent_button.setText("▼")
        self.recent_button.setProperty("class", "recent-button")
        self.recent_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recent_button.setFixedSize(QSize(24, 32))
        h_layout.addWidget(self.recent_button)

        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setProperty("class", "browse-button")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setFixedSize(QSize(80, 32))
        h_layout.addWidget(self.browse_button)

        layout.addWidget(h_layout_widget)

        # Connect signals
        self.browse_button.clicked.connect(self._on_browse_clicked)
        self.recent_button.clicked.connect(self._show_recent_menu)
        self.directory_input.textChanged.connect(self._on_text_changed)
        self.directory_input.setDragEnabled(True)
        self.directory_input.setAcceptDrops(True)
        self.directory_input.dragEnterEvent = self.dragEnterEvent
        self.directory_input.dropEvent = self.dropEvent
        self.directory_input.setContextMenuPolicy(
            Qt.ContextMenuPolicy.CustomContextMenu
        )
        self.directory_input.customContextMenuRequested.connect(self._show_context_menu)

        # Install event filter for Enter key detection
        self.directory_input.installEventFilter(self)

        # Keyboard shortcuts
        self.shortcut_browse = QShortcut(QKeySequence("Ctrl+O"), self)
        self.shortcut_browse.activated.connect(self._on_browse_clicked)
        self.shortcut_focus = QShortcut(QKeySequence("Ctrl+D"), self)
        self.shortcut_focus.activated.connect(lambda: self.directory_input.setFocus())

    def _show_recent_menu(self) -> None:
        """Create and show the context menu for recent directories."""
        menu = QMenu(self)

        if not self.recent_directories:
            action = menu.addAction("No recent directories")
            action.setEnabled(False)
        else:
            for directory in self.recent_directories:
                # AC: Display friendly names: /home/user/Documents → "Documents"
                path_obj = Path(directory)
                friendly_name = path_obj.name if path_obj.name else str(path_obj)
                action = menu.addAction(f"{friendly_name} ({directory})")
                action.setData(directory)
                action.triggered.connect(
                    lambda checked, d=directory: self.set_directory(Path(d))
                )

            menu.addSeparator()
            clear_action = menu.addAction("Clear History")
            clear_action.triggered.connect(self._clear_recent_history)

        # Show the menu below the button
        menu.exec(
            self.recent_button.mapToGlobal(self.recent_button.rect().bottomLeft())
        )

    def _show_context_menu(self, pos):
        """Show context menu for recent directories on right-click."""
        menu = QMenu(self)
        if self.recent_directories:
            for directory in self.recent_directories:
                path_obj = Path(directory)
                friendly_name = path_obj.name if path_obj.name else str(path_obj)
                action = menu.addAction(f"{friendly_name} ({directory})")
                action.setData(directory)
                action.triggered.connect(
                    lambda checked, d=directory: self.set_directory(Path(d))
                )
            menu.addSeparator()
            clear_action = menu.addAction("Clear History")
            clear_action.triggered.connect(self._clear_recent_history)
        else:
            action = menu.addAction("No recent directories")
            action.setEnabled(False)
        menu.exec(self.directory_input.mapToGlobal(pos))

    def _clear_recent_history(self) -> None:
        """Clear the recent directories list and save."""
        self.recent_directories = []
        self._save_recent_directories()
        logger.debug("Recent directory history cleared")

    def _on_browse_clicked(self) -> None:
        """Handle browse button click to open native directory selection dialog."""
        logger.debug("Browse button clicked - opening QFileDialog")

        dialog_title = "Select Search Directory"
        current_dir = str(self.get_directory())

        selected_dir = QFileDialog.getExistingDirectory(
            self,
            dialog_title,
            current_dir,
            QFileDialog.Option.ShowDirsOnly | QFileDialog.Option.DontResolveSymlinks,
        )

        if selected_dir:
            logger.debug(f"Directory selected: {selected_dir}")
            selected_path = Path(selected_dir)
            self.set_directory(selected_path)
            self._add_to_recent_directories(selected_path)
        else:
            logger.debug("Directory selection cancelled")

    def _setup_style(self) -> None:
        """Setup widget styling."""
        self.setStyleSheet(
            """
            QLabel.directory-label {
                font-size: 12px;
                font-weight: bold;
                color: #666666;
                margin-bottom: 4px;
            }

            QLineEdit.directory-input {
                font-size: 14px;
                font-family: system-ui, -apple-system, sans-serif;
                padding: 4px 8px;
                border: 2px solid #cccccc;
                border-radius: 4px;
                background: rgba(255, 255, 255, 0.95);
                color: #333333;
                selection-background-color: #0078d4;
            }

            QLineEdit.directory-input:focus {
                border-color: #0078d4;
                outline: none;
            }

            QPushButton.browse-button {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #0078d4;
                border-radius: 4px;
                background-color: #0078d4;
                color: white;
            }

            QPushButton.browse-button:hover {
                background-color: #005a9e;
                border-color: #005a9e;
            }

            QToolButton.recent-button {
                border: 2px solid #cccccc;
                border-left: none;
                border-radius: 0 4px 4px 0;
                background: rgba(255, 255, 255, 0.95);
                color: #666666;
                font-weight: bold;
            }

            QToolButton.recent-button:hover {
                background: #eeeeee;
            }
        """
        )
        self.setObjectName("directorySelectorWidget")

    def _load_recent_directories(self) -> None:
        """Load recent directories from configuration."""
        if not self.config_manager:
            return

        try:
            # Constraint: Store and retrieve recent directories from
            # ConfigManager (max 5)
            self.recent_directories = self.config_manager.get("recent.directories", [])[
                :5
            ]
            logger.debug(f"Loaded {len(self.recent_directories)} recent directories")
        except Exception as e:
            logger.error(f"Error loading recent directories: {e}")
            self.recent_directories = []

    def _setup_completer(self) -> None:
        """Setup auto-completer with common paths and recent directories."""
        # AC 2.3: Auto-complete common paths (home, documents, desktop)
        home = os.path.expanduser("~")
        common_paths = [
            home,
            os.path.join(home, "Documents"),
            os.path.join(home, "Desktop"),
        ]

        # Include recent directories in addition
        all_options = common_paths + self.recent_directories

        if not all_options:
            return

        completer = QCompleter(all_options)
        completer.setCaseSensitivity(Qt.CaseSensitivity.CaseInsensitive)
        completer.setFilterMode(Qt.MatchFlag.MatchContains)
        completer.setCompletionMode(QCompleter.CompletionMode.PopupCompletion)

        self.directory_input.setCompleter(completer)

        logger.debug("Directory auto-completer setup completed")

    def _save_recent_directories(self) -> None:
        """Save recent directories to configuration."""
        if not self.config_manager:
            return

        try:
            self.config_manager.set("recent.directories", self.recent_directories)
            self.config_manager.save()
            logger.debug("Recent directories saved")
        except Exception as e:
            logger.error(f"Error saving recent directories: {e}")

    def _add_to_recent_directories(self, directory: Path) -> None:
        """Add a directory to the recent list and save.

        Args:
            directory: Path object of the directory to add.
        """
        dir_str = str(directory)
        if not dir_str or not directory.is_dir():
            return

        # Remove if already exists
        if dir_str in self.recent_directories:
            self.recent_directories.remove(dir_str)

        # Add to beginning
        self.recent_directories.insert(0, dir_str)

        # Trim to maximum size (max 5 entries)
        self.recent_directories = self.recent_directories[:5]

        self._save_recent_directories()
        self._setup_completer()
        logger.debug(f"Added to recent directories: '{dir_str}'")

    def _set_default_directory(self) -> None:
        """Set the default directory to the user's home directory."""
        # AC: Default directory: user's home directory (~ or %USERPROFILE%)
        # Dev Note: Use os.path.expanduser
        home_dir_path = normalize_path("~")
        self.directory_input.setText(str(home_dir_path))
        self.directory_changed.emit(home_dir_path)

    def _on_text_changed(self, text: str) -> None:
        """Handle text change events, normalize, validate, and emit signal."""
        if not text.strip():
            self.directory_input.setToolTip("")
            self.directory_input.setProperty("state", "normal")
            self.directory_input.style().unpolish(self.directory_input)
            self.directory_input.style().polish(self.directory_input)
            self.directory_changed.emit(Path(""))
            return

        try:
            # 1. Normalize path (expands ~, $HOME, etc.)
            normalized_path = normalize_path(text)

            # 2. Validate directory
            error_message = validate_directory(normalized_path)

            if error_message:
                # Show error state for invalid paths (red border, tooltip)
                self.directory_input.setToolTip(error_message)
                self.directory_input.setProperty("state", "error")
                self.directory_input.style().unpolish(self.directory_input)
                self.directory_input.style().polish(self.directory_input)
                self.directory_changed.emit(
                    normalized_path
                )  # Emit even on error to allow search engine to handle it
            else:
                # Valid path
                self.directory_input.setToolTip(str(normalized_path))
                self.directory_input.setProperty("state", "normal")
                self.directory_input.style().unpolish(self.directory_input)
                self.directory_input.style().polish(self.directory_input)
                self.directory_changed.emit(normalized_path)

        except Exception as e:
            logger.error(f"Error during path validation: {e}")
            self.directory_input.setToolTip(f"Internal error: {e}")
            self.directory_input.setProperty("state", "error")
            self.directory_input.style().unpolish(self.directory_input)
            self.directory_input.style().polish(self.directory_input)
            self.directory_changed.emit(Path(text))

    def get_directory(self) -> Path:
        """Get the current directory path as a Path object."""
        return Path(self.directory_input.text())

    def set_directory(self, path: Path) -> None:
        """Set the directory input text from a Path object."""
        self.directory_input.setText(str(path))
        self.directory_changed.emit(path)

    def set_read_only(self, read_only: bool) -> None:
        """Set the directory input to read-only mode during search."""
        self.directory_input.setReadOnly(read_only)
        self.browse_button.setEnabled(not read_only)
        self.recent_button.setEnabled(not read_only)

    def dragEnterEvent(self, event: QDragEnterEvent) -> None:
        """Handle drag enter event to accept directory drops."""
        if event.mimeData().hasUrls():
            # Check if the drop contains a single directory
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                path = Path(urls[0].toLocalFile())
                if path.is_dir():
                    event.acceptProposedAction()

    def eventFilter(self, obj, event):
        """Event filter to detect Enter key in directory input."""
        if obj == self.directory_input and event.type() == QEvent.Type.KeyPress:
            if event.key() in (Qt.Key.Key_Return, Qt.Key.Key_Enter):
                self.enter_pressed.emit()
                return True  # Consume the event
        return super().eventFilter(obj, event)


class SearchControlWidget(QWidget):
    """Widget providing search initiation and control buttons.

    This widget provides a search/stop button with state management and
    keyboard shortcuts for controlling search operations.

    Signals:
        search_requested(): Emitted when search is initiated
        search_stopped(): Emitted when search is stopped
    """

    # Signals
    search_requested = pyqtSignal()
    search_stopped = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize search control widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # State
        self._state = SearchState.IDLE
        self._query_empty = True

        # Setup UI
        self._setup_ui()
        self._setup_style()
        self._setup_shortcuts()

        # Update initial state
        self._update_button_state()

        logger.debug("SearchControlWidget initialized")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Main layout
        layout = QHBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Search control button
        self.search_button = QPushButton("Search")
        self.search_button.setProperty("class", "search-control-button")
        self.search_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.search_button.setFixedSize(QSize(80, 32))  # AC: 80px wide, 32px height
        self.search_button.clicked.connect(self._on_button_clicked)

        layout.addWidget(self.search_button)

        # Set widget size policy
        self.setFixedSize(QSize(80, 32))

    def _setup_style(self) -> None:
        """Setup widget styling."""
        self.setStyleSheet(
            """
            QPushButton.search-control-button {
                font-size: 14px;
                font-weight: bold;
                border: 2px solid #0078d4;
                border-radius: 4px;
                background-color: #0078d4;
                color: white;
                padding: 4px 8px;
            }

            QPushButton.search-control-button:hover {
                background-color: #005a9e;
                border-color: #005a9e;
            }

            QPushButton.search-control-button:pressed {
                background-color: #004578;
                border-color: #004578;
            }

            QPushButton.search-control-button:disabled {
                background-color: #cccccc;
                border-color: #cccccc;
                color: #666666;
            }

            QPushButton.search-control-button[state="stop"] {
                background-color: #d13438;
                border-color: #d13438;
            }

            QPushButton.search-control-button[state="stop"]:hover {
                background-color: #b91c1c;
                border-color: #b91c1c;
            }

            QPushButton.search-control-button[state="stop"]:pressed {
                background-color: #991b1b;
                border-color: #991b1b;
            }
        """
        )

        self.setObjectName("searchControlWidget")

    def _setup_shortcuts(self) -> None:
        """Setup keyboard shortcuts via key press event handling."""
        # Shortcuts are handled in keyPressEvent for better testability
        pass

    def _on_button_clicked(self) -> None:
        """Handle search button click."""
        if (
            self._state == SearchState.IDLE
            or self._state == SearchState.COMPLETED
            or self._state == SearchState.ERROR
        ):
            self._on_search_shortcut()
        elif self._state == SearchState.RUNNING:
            self._on_stop_shortcut()

    def _on_search_shortcut(self) -> None:
        """Handle search initiation."""
        if self._can_start_search():
            self.search_requested.emit()
            logger.debug("Search requested via button/shortcut")

    def _on_stop_shortcut(self) -> None:
        """Handle search stop."""
        if self._state == SearchState.RUNNING:
            self.search_stopped.emit()
            logger.debug("Search stop requested via button/shortcut")

    def _focus_button(self) -> None:
        """Focus the search button."""
        self.search_button.setFocus()
        logger.debug("Search button focused via Ctrl+S")

    def _can_start_search(self) -> bool:
        """Check if search can be started."""
        return not self._query_empty and self._state in (
            SearchState.IDLE,
            SearchState.COMPLETED,
            SearchState.ERROR,
        )

    def _update_button_state(self) -> None:
        """Update button text, style, and enabled state based on current state."""
        if self._state == SearchState.IDLE:
            self.search_button.setText("Search")
            self.search_button.setProperty("state", "search")
            self.search_button.setEnabled(self._can_start_search())

        elif self._state == SearchState.RUNNING:
            self.search_button.setText("Stop")
            self.search_button.setProperty("state", "stop")
            self.search_button.setEnabled(True)

        elif self._state == SearchState.STOPPING:
            self.search_button.setText("Stop")
            self.search_button.setProperty("state", "stop")
            self.search_button.setEnabled(False)

        elif self._state == SearchState.COMPLETED:
            self.search_button.setText("Search")
            self.search_button.setProperty("state", "search")
            self.search_button.setEnabled(self._can_start_search())

        elif self._state == SearchState.ERROR:
            self.search_button.setText("Search")
            self.search_button.setProperty("state", "search")
            self.search_button.setEnabled(self._can_start_search())

        # Apply style changes
        style = self.search_button.style()
        if style:
            style.unpolish(self.search_button)
            style.polish(self.search_button)

    def set_state(self, state: SearchState) -> None:
        """Set the search control state.

        Args:
            state: New search state
        """
        if self._state != state:
            old_state = self._state
            self._state = state
            self._update_button_state()
            logger.debug(f"Search state changed: {old_state.value} → {state.value}")

    def set_query_empty(self, is_empty: bool) -> None:
        """Set whether the search query is empty.

        Args:
            is_empty: True if query is empty, False otherwise
        """
        if self._query_empty != is_empty:
            self._query_empty = is_empty
            self._update_button_state()
            logger.debug(f"Query empty state changed: {is_empty}")

    def get_state(self) -> SearchState:
        """Get current search state.

        Returns:
            Current SearchState
        """
        return self._state

    def keyPressEvent(self, event) -> None:
        """Handle key press events for shortcuts."""
        # Ctrl+Enter: Start search
        if (
            event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter
        ) and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self._on_search_shortcut()
            event.accept()
            return

        # Escape: Stop search if running
        if event.key() == Qt.Key.Key_Escape:
            self._on_stop_shortcut()
            event.accept()
            return

        # Ctrl+S: Focus search button
        if (
            event.key() == Qt.Key.Key_S
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self._focus_button()
            event.accept()
            return

        # Pass other events to parent
        super().keyPressEvent(event)

    def dropEvent(self, event: QDropEvent) -> None:
        """Handle drop event to set the directory path."""
        if event.mimeData().hasUrls():
            urls = event.mimeData().urls()
            if len(urls) == 1 and urls[0].isLocalFile():
                path = Path(urls[0].toLocalFile())
                if path.is_dir():
                    self.set_directory(path)
                    self._add_to_recent_directories(path)
                    event.acceptProposedAction()


class ProgressWidget(QWidget):
    """Widget displaying search progress with bar, text, spinner, and counter.

    This widget provides visual feedback during search operations including
    progress bar, status text, animated spinner, and file scan counter.

    Signals:
        progress_updated(int, str): Emitted when progress is updated
    """

    # Signals
    progress_updated = pyqtSignal(int, str)  # files_scanned, current_dir

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize progress widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Progress state
        self.files_scanned = 0
        self.current_dir = ""
        self.is_visible = False
        self.is_determinate = False
        self.total_files_estimate = 0
        self.start_time = 0

        # Animation state
        self.spinner_angle = 0
        self.animation_timer = QTimer()
        self.animation_timer.timeout.connect(self._animate_spinner)

        # Setup UI
        self._setup_ui()
        self._setup_style()

        # Initially hidden
        self.setVisible(False)
        # Set minimum size to 0 when hidden to prevent layout issues
        self.setMinimumSize(QSize(0, 0))

        logger.debug("ProgressWidget initialized")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate by default
        self.progress_bar.setFixedHeight(6)  # Thin progress bar
        self.progress_bar.setTextVisible(False)
        layout.addWidget(self.progress_bar)

        # Bottom row: spinner + text + counter
        bottom_layout = QHBoxLayout()
        bottom_layout.setContentsMargins(0, 0, 0, 0)
        bottom_layout.setSpacing(8)

        # Spinner
        self.spinner_label = QLabel("⟳")
        self.spinner_label.setProperty("class", "spinner")
        self.spinner_label.setFixedSize(QSize(16, 16))
        bottom_layout.addWidget(self.spinner_label)

        # Progress text
        self.progress_text = QLabel("Initializing search...")
        self.progress_text.setProperty("class", "progress-text")
        bottom_layout.addWidget(self.progress_text, 1)  # Stretch

        # File counter
        self.file_counter = QLabel("0 files scanned")
        self.file_counter.setProperty("class", "file-counter")
        bottom_layout.addWidget(self.file_counter)

        layout.addLayout(bottom_layout)

    def _setup_style(self) -> None:
        """Setup widget styling."""
        self.setStyleSheet(
            """
            QWidget#progressWidget {
                background: transparent;
            }

            QProgressBar {
                border: none;
                border-radius: 3px;
                background: rgba(255, 255, 255, 0.1);
            }

            QProgressBar::chunk {
                background: #0078d4;
                border-radius: 3px;
            }

            QLabel.spinner {
                color: #0078d4;
                font-size: 14px;
                font-weight: bold;
            }

            QLabel.progress-text {
                color: #666666;
                font-size: 12px;
                font-family: system-ui, -apple-system, sans-serif;
            }

            QLabel.file-counter {
                color: #666666;
                font-size: 12px;
                font-family: system-ui, -apple-system, sans-serif;
                font-weight: bold;
            }
        """
        )
        self.setObjectName("progressWidget")

    def _animate_spinner(self) -> None:
        """Animate the spinner by rotating through characters."""
        spinner_chars = ["⟳", "⟲", "⟱", "⟰"]
        self.spinner_angle = (self.spinner_angle + 1) % len(spinner_chars)
        self.spinner_label.setText(spinner_chars[self.spinner_angle])

    def _format_file_count(self, count: int) -> str:
        """Format file count with thousands separator.

        Args:
            count: Number of files

        Returns:
            Formatted string
        """
        return "{:,} files scanned".format(count)

    def _truncate_path(self, path: str, max_length: int = 40) -> str:
        """Truncate path if too long.

        Args:
            path: Path to truncate
            max_length: Maximum length

        Returns:
            Truncated path
        """
        if len(path) <= max_length:
            return path
        start = -(max_length - 3)
        return "..." + path[start:]

    def _estimate_remaining_time(self, files_scanned: int) -> str:
        """Estimate remaining time based on progress.

        Args:
            files_scanned: Number of files scanned so far

        Returns:
            Formatted remaining time string or empty if not estimable
        """
        if (
            not self.is_determinate
            or self.total_files_estimate == 0
            or files_scanned == 0
        ):
            return ""

        elapsed = time.time() - self.start_time
        if elapsed < 1:
            return ""

        progress_ratio = files_scanned / self.total_files_estimate
        if progress_ratio < 0.1:  # Need some progress to estimate
            return ""

        total_estimated = elapsed / progress_ratio
        remaining = total_estimated - elapsed

        if remaining < 60:
            return f"About {int(remaining)}s remaining"
        elif remaining < 3600:
            return f"About {int(remaining / 60)}m remaining"
        else:
            return f"About {int(remaining / 3600)}h remaining"

    def update_progress(self, files_scanned: int, current_dir: str) -> None:
        """Update progress display.

        Args:
            files_scanned: Number of files scanned so far
            current_dir: Current directory being scanned
        """
        self.files_scanned = files_scanned
        self.current_dir = current_dir

        # Update file counter
        self.file_counter.setText(self._format_file_count(files_scanned))

        # Update progress text
        truncated_dir = self._truncate_path(current_dir)
        remaining_time = self._estimate_remaining_time(files_scanned)

        if self.is_determinate and self.total_files_estimate > 0:
            percentage = min(
                100, int((files_scanned / self.total_files_estimate) * 100)
            )
            self.progress_bar.setValue(percentage)
            time_str = f" | {remaining_time}" if remaining_time else ""
            self.progress_text.setText(
                f"Scanning {truncated_dir}... ({percentage}%){time_str}"
            )
        else:
            self.progress_text.setText(f"Scanning {truncated_dir}...")

        # Emit signal
        self.progress_updated.emit(files_scanned, current_dir)

        logger.debug(f"Progress updated: {files_scanned} files, dir: {current_dir}")

    def set_determinate_mode(self, total_files: int) -> None:
        """Set progress bar to determinate mode.

        Args:
            total_files: Estimated total number of files
        """
        self.is_determinate = True
        self.total_files_estimate = total_files
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        logger.debug(f"Set determinate mode with {total_files} total files")

    def set_indeterminate_mode(self) -> None:
        """Set progress bar to indeterminate mode."""
        self.is_determinate = False
        self.total_files_estimate = 0
        self.progress_bar.setRange(0, 0)  # Indeterminate
        logger.debug("Set indeterminate mode")

    def show_progress(self) -> None:
        """Show the progress widget with animation."""
        if not self.is_visible:
            self.is_visible = True
            self.start_time = time.time()
            self.setVisible(True)
            self.animation_timer.start(200)  # 200ms animation interval
            logger.debug("Progress widget shown")

    def hide_progress(self) -> None:
        """Hide the progress widget with fade out."""
        if self.is_visible:
            self.is_visible = False
            self.animation_timer.stop()
            self.setVisible(False)
            # Reset state
            self.files_scanned = 0
            self.current_dir = ""
            self.progress_text.setText("Search completed")
            self.file_counter.setText("0 files scanned")
            logger.debug("Progress widget hidden")

    def set_error_state(self, error_message: str) -> None:
        """Set error state display.

        Args:
            error_message: Error message to display
        """
        self.progress_text.setText(f"Error: {error_message}")
        self.spinner_label.setText("❌")
        self.animation_timer.stop()
        logger.debug(f"Error state set: {error_message}")

    def set_total_estimate(self, total_files: int) -> None:
        """Set total file estimate for determinate progress.

        Args:
            total_files: Estimated total number of files
        """
        if total_files > 0:
            self.set_determinate_mode(total_files)
        else:
            self.set_indeterminate_mode()
        logger.debug(f"Total estimate set: {total_files} files")

    def set_completed_state(self, total_files: int) -> None:
        """Set completed state display.

        Args:
            total_files: Total number of files scanned
        """
        self.progress_text.setText("Search completed")
        self.file_counter.setText(self._format_file_count(total_files))
        self.spinner_label.setText("✅")
        self.animation_timer.stop()
        if self.is_determinate:
            self.progress_bar.setValue(100)
        logger.debug(f"Completed state set: {total_files} files")

    def sizeHint(self) -> QSize:
        """Override size hint to return zero when hidden."""
        if not self.is_visible:
            return QSize(0, 0)
        return super().sizeHint()

    def minimumSizeHint(self) -> QSize:
        """Override minimum size hint to return zero when hidden."""
        if not self.is_visible:
            return QSize(0, 0)
        return super().minimumSizeHint()


class StatusWidget(QWidget):
    """Widget displaying search status information including results count,
    summary, and error states.

    This widget provides clear status information about search results, including
    results count with color coding, search summary with duration, zero results state
    with suggestions, and error states with recovery suggestions.

    Signals:
        status_updated(str, int): Emitted when status is updated
    """

    # Signals
    status_updated = pyqtSignal(str, int)  # status_message, result_count

    def __init__(self, parent: Optional[QWidget] = None):
        """Initialize status widget.

        Args:
            parent: Parent widget (optional)
        """
        super().__init__(parent)

        # Status state
        self.result_count = 0
        self.search_query = ""
        self.search_directory = ""
        self.search_duration = 0.0
        self.current_status = "ready"  # ready, searching, completed, error

        # Setup UI
        self._setup_ui()
        self._setup_style()

        # Set initial status
        # Status history for debug mode (last 100 messages)
        self.status_history: list[str] = []

        self.update_status("ready", 0)

        logger.debug("StatusWidget initialized")

    def _setup_ui(self) -> None:
        """Setup user interface components."""
        # Main layout
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)
        self.setLayout(layout)

        # Results count label (prominent)
        self.results_count_label = QLabel("Ready")
        self.results_count_label.setProperty("class", "results-count")
        layout.addWidget(self.results_count_label)

        # Search summary label
        self.summary_label = QLabel("")
        self.summary_label.setProperty("class", "status-summary")
        layout.addWidget(self.summary_label)

    def _setup_style(self) -> None:
        """Setup widget styling."""
        self.setStyleSheet(
            """
            QWidget#statusWidget {
                background: transparent;
            }

            QLabel.results-count {
                font-size: 16px;
                font-weight: bold;
                color: #666666;
                margin-bottom: 4px;
            }

            QLabel.results-count[state="success"] {
                color: #107c10;
            }

            QLabel.results-count[state="zero"] {
                color: #ff8c00;
            }

            QLabel.results-count[state="error"] {
                color: #d13438;
            }

            QLabel.status-summary {
                font-size: 12px;
                color: #666666;
                font-family: system-ui, -apple-system, sans-serif;
            }
        """
        )
        self.setObjectName("statusWidget")

    def _format_result_count(self, count: int) -> str:
        """Format result count with thousands separator.

        Args:
            count: Number of results

        Returns:
            Formatted string
        """
        # Use Python's built-in thousands separator
        return "{:,} files found".format(count)

    def _format_duration(self, duration: float) -> str:
        """Format duration in human-readable format.

        Args:
            duration: Duration in seconds

        Returns:
            Formatted duration string
        """
        return "{:.1f}s".format(duration)

    def update_status(
        self,
        status: str,
        result_count: int = 0,
        query: str = "",
        directory: str = "",
        duration: float = 0.0,
    ) -> None:
        """Update status display.

        Args:
            status: Status type (ready, searching, completed, error)
            result_count: Number of results found
            query: Search query
            directory: Search directory
            duration: Search duration in seconds
        """
        self.current_status = status
        self.result_count = result_count
        self.search_query = query
        self.search_directory = directory
        self.search_duration = duration

        # Update results count label
        if status == "ready":
            self.results_count_label.setText(self.tr("Ready"))
            self.results_count_label.setProperty("state", "normal")
        elif status == "searching":
            self.results_count_label.setText(self.tr("Searching..."))
            self.results_count_label.setProperty("state", "normal")
        elif status == "completed":
            if result_count == 0:
                self.results_count_label.setText(self.tr("No files found"))
                self.results_count_label.setProperty("state", "zero")
            elif result_count > 0:
                count_text = self._format_result_count(result_count)
                self.results_count_label.setText(count_text)
                self.results_count_label.setProperty("state", "success")
            else:
                self.results_count_label.setText(self.tr("Search completed"))
                self.results_count_label.setProperty("state", "normal")
        elif status == "error":
            self.results_count_label.setText(self.tr("Error"))
            self.results_count_label.setProperty("state", "error")
        else:
            self.results_count_label.setText(status)
            self.results_count_label.setProperty("state", "normal")

        # Apply style changes
        style = self.results_count_label.style()
        if style:
            style.unpolish(self.results_count_label)
            style.polish(self.results_count_label)

        # Update summary label
        summary_text = self._get_summary_text(
            status, result_count, query, directory, duration
        )
        self.summary_label.setText(summary_text)

        # Audio notification for search completion if enabled
        if status == "completed":
            try:
                from filesearch.core.config_manager import ConfigManager

                config = ConfigManager()
                if config.get("ui.audio_notification_on_search_complete", False):
                    QApplication.beep()
                # Persist last search summary
                config.set("ui.last_search_summary", summary_text)
                config.save()
            except Exception as e:
                logger.warning(f"Search completion handling failed: {e}")

        # Emit signal
        self.status_updated.emit(status, result_count)

        # Add to status history for debug mode (last 100 messages)
        message = (
            f"{status}: {self.results_count_label.text()} - {summary_text}".strip()
        )
        self.status_history.append(message)
        if len(self.status_history) > 100:
            self.status_history.pop(0)

        logger.debug(f"Status updated: {status}, {result_count} results")

    def get_status_history(self) -> list[str]:
        """Get status history for debug mode.

        Returns:
            List of last 100 status messages
        """
        return self.status_history.copy()

    def copy_status_to_clipboard(self) -> None:
        """Copy current status message to clipboard."""
        status_text = (
            f"{self.results_count_label.text()} {self.summary_label.text()}".strip()
        )
        clipboard = QApplication.clipboard()
        if clipboard:
            clipboard.setText(status_text)

    def contextMenuEvent(self, event) -> None:
        """Show context menu on right-click."""
        menu = QMenu(self)
        copy_action = menu.addAction("Copy Status")
        copy_action.triggered.connect(self.copy_status_to_clipboard)
        menu.exec(event.globalPos())

    def _get_summary_text(
        self,
        status: str,
        result_count: int,
        query: str,
        directory: str,
        duration: float,
    ) -> str:
        """Get summary text based on status.

        Args:
            status: Status type
            result_count: Number of results
            query: Search query
            directory: Search directory
            duration: Search duration

        Returns:
            Summary text
        """
        if status == "ready":
            return ""
        elif status == "searching":
            if directory:
                return self.tr("Searching in {directory}...").format(
                    directory=directory
                )
            return self.tr("Initializing search...")
        elif status == "completed":
            if result_count == 0:
                if query:
                    return self.tr(
                        "No files found matching '{query}'. Try a broader search "
                        "term or different directory."
                    ).format(query=query)
                return self.tr("No files found.")
            elif result_count > 0:
                duration_str = self._format_duration(duration)
                if directory and query:
                    return self.tr(
                        "Found {result_count} matches in {directory} for "
                        "'{query}' ({duration_str})"
                    ).format(
                        result_count=result_count,
                        directory=directory,
                        query=query,
                        duration_str=duration_str,
                    )
                elif directory:
                    return self.tr(
                        "Found {result_count} matches in {directory} ({duration_str})"
                    ).format(
                        result_count=result_count,
                        directory=directory,
                        duration_str=duration_str,
                    )
                elif query:
                    return self.tr(
                        "Found {result_count} matches for '{query}' ({duration_str})"
                    ).format(
                        result_count=result_count,
                        query=query,
                        duration_str=duration_str,
                    )
                else:
                    return self.tr("Search completed in {duration_str}").format(
                        duration_str=duration_str
                    )
        elif status == "error":
            return self.tr("Please select a different directory and try again.")
        else:
            return ""

    def set_error_message(self, error_message: str) -> None:
        """Set error message display.

        Args:
            error_message: Error message to display
        """
        self.results_count_label.setText("Error")
        self.results_count_label.setProperty("state", "error")

        # Apply style changes
        style = self.results_count_label.style()
        if style:
            style.unpolish(self.results_count_label)
            style.polish(self.results_count_label)

        self.summary_label.setText(error_message)

        logger.debug(f"Error message set: {error_message}")

    def clear_status(self) -> None:
        """Clear status display."""
        self.update_status("ready", 0)

    def get_current_status(self) -> str:
        """Get current status.

        Returns:
            Current status string
        """
        return self.current_status

    def get_result_count(self) -> int:
        """Get current result count.

        Returns:
            Current result count
        """
        return self.result_count
