"""Search input widget with history, auto-complete, and visual feedback."""

from typing import List, Optional

from loguru import logger
from PyQt6.QtCore import QSize, Qt, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QCompleter,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager


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

    def minimumSizeHint(self) -> QSize:
        """Return minimum size hint."""
        return QSize(400, 60)

    def sizeHint(self) -> QSize:
        """Return size hint."""
        return QSize(400, 60)

    def _setup_ui(self) -> None:
        """Setup user interface components as a unified search bar.

        Layout: [search-icon] [QLineEdit] [clear-btn] [loading-indicator]
        All wrapped in a single styled container.
        """
        # Main layout — no extra margins, the container IS the widget
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.setLayout(layout)

        # Keep label reference for backward compat but hide it
        self.label = QLabel("Search files and folders")
        self.label.setProperty("class", "search-label")
        self.label.setVisible(False)
        layout.addWidget(self.label)

        # Unified search bar container
        search_container = QWidget()
        search_container.setObjectName("searchBarContainer")
        search_layout = QHBoxLayout()
        search_layout.setContentsMargins(10, 0, 6, 0)
        search_layout.setSpacing(6)
        search_container.setLayout(search_layout)

        # Search icon
        try:
            import qtawesome as qta

            from filesearch.ui.theme import Colors as _C

            self.search_icon = QLabel()
            self.search_icon.setPixmap(
                qta.icon("mdi6.magnify", color=_C.TEXT_TERTIARY).pixmap(18, 18)
            )
            self.search_icon.setFixedSize(18, 18)
        except Exception:
            self.search_icon = QLabel("\U0001f50d")
            self.search_icon.setFixedSize(18, 18)
        search_layout.addWidget(self.search_icon)

        # Search input field
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search files and folders...")
        self.search_input.setMaxLength(self.MAX_SEARCH_LENGTH)
        self.search_input.setProperty("class", "search-input")
        self.search_input.setMinimumHeight(36)

        # Set accessibility attributes
        self.search_input.setAccessibleName("Search input")
        self.search_input.setAccessibleDescription(
            "Enter filename or partial name to search for files and folders"
        )
        self.search_input.setAlignment(Qt.AlignmentFlag.AlignVCenter)
        search_layout.addWidget(self.search_input, 1)

        # Clear button
        try:
            import qtawesome as qta

            from filesearch.ui.theme import Colors as _C

            self.clear_button = QToolButton()
            self.clear_button.setIcon(qta.icon("mdi6.close", color=_C.TEXT_TERTIARY))
        except Exception:
            self.clear_button = QToolButton()
            self.clear_button.setText("\u2715")
        self.clear_button.setProperty("class", "clear-button")
        self.clear_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self.clear_button.setVisible(False)
        self.clear_button.clicked.connect(self.clear_text)
        self.clear_button.setFixedSize(24, 24)
        search_layout.addWidget(self.clear_button)

        # Loading indicator
        self.loading_indicator = QLabel("\u27f3")
        self.loading_indicator.setProperty("class", "loading-indicator")
        self.loading_indicator.setVisible(False)
        self.loading_indicator.setFixedSize(24, 24)
        search_layout.addWidget(self.loading_indicator)

        layout.addWidget(search_container)

        # Connect signals
        self.connect_signals()

        logger.debug("UI setup completed")

    def _setup_style(self) -> None:
        """Setup widget styling via centralized theme."""
        self.setObjectName("searchInputWidget")

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
