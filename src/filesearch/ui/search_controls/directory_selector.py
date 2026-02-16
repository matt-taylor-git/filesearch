"""Directory selector widget for choosing search directories."""

import os
from pathlib import Path
from typing import List, Optional

from loguru import logger
from PyQt6.QtCore import QEvent, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QDragEnterEvent, QKeySequence, QShortcut
from PyQt6.QtWidgets import (
    QCompleter,
    QFileDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.file_utils import normalize_path, validate_directory


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
        self.directory_input.setMinimumHeight(36)
        h_layout.addWidget(self.directory_input)

        # Dropdown button for recent directories
        self.recent_button = QToolButton()
        self.recent_button.setText("\u25bc")
        self.recent_button.setProperty("class", "recent-button")
        self.recent_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.recent_button.setFixedSize(QSize(28, 36))
        h_layout.addWidget(self.recent_button)

        # Browse button
        self.browse_button = QPushButton("Browse...")
        self.browse_button.setProperty("class", "browse-button")
        self.browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.browse_button.setFixedSize(QSize(96, 36))
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
                # AC: Display friendly names: /home/user/Documents -> "Documents"
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
        """Setup widget styling via centralized theme."""
        self.setObjectName("directorySelectorWidget")

    def _load_recent_directories(self) -> None:
        """Load recent directories from configuration."""
        if not self.config_manager:
            return

        try:
            # Constraint: Store and retrieve recent directories from
            # ConfigManager (max 5)
            self.recent_directories = self.config_manager.get(
                "recent.directories", []
            )[:5]
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
