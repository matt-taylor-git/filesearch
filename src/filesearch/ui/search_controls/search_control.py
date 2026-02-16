"""Search control button widget for initiating and stopping searches."""

from pathlib import Path
from typing import Optional

from loguru import logger
from PyQt6.QtCore import QSize, Qt, pyqtSignal
from PyQt6.QtGui import QDropEvent
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QPushButton,
    QWidget,
)

from filesearch.ui.search_controls.search_state import SearchState


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
        self.search_button.setFixedSize(QSize(88, 36))
        self.search_button.clicked.connect(self._on_button_clicked)

        layout.addWidget(self.search_button)

        # Set widget size policy
        self.setFixedSize(QSize(88, 36))

    def _setup_style(self) -> None:
        """Setup widget styling via centralized theme."""
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
            logger.debug(
                f"Search state changed: {old_state.value} \u2192 {state.value}"
            )

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
