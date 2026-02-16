"""Progress widget for displaying search progress."""

import time
from typing import Optional

from loguru import logger
from PyQt6.QtCore import QSize, QTimer, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QVBoxLayout,
    QWidget,
)


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
        self.spinner_label = QLabel("\u27f3")
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
        """Setup widget styling via centralized theme."""
        self.setObjectName("progressWidget")

    def _animate_spinner(self) -> None:
        """Animate the spinner by rotating through characters."""
        spinner_chars = ["\u27f3", "\u27f2", "\u27f1", "\u27f0"]
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
        self.spinner_label.setText("\u274c")
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
        self.spinner_label.setText("\u2705")
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
