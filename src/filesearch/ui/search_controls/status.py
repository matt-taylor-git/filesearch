"""Status widget for displaying search status and results count."""

from typing import Optional

from loguru import logger
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QLabel,
    QMenu,
    QVBoxLayout,
    QWidget,
)


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
        """Setup widget styling via centralized theme."""
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
