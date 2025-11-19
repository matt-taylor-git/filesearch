"""Properties dialog for displaying detailed file information.

This module implements a modal dialog that shows comprehensive file properties
including size, modification dates, permissions, and checksums.
"""

import hashlib
import math
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, Union

from loguru import logger
from PyQt6.QtCore import Qt, QThread, pyqtSignal
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.exceptions import FileSearchError


class ChecksumWorker(QThread):
    """Worker thread for calculating file checksums in the background.

    Signals:
        checksum_calculated(hash_type: str, hash_value: str): Emitted when checksum is calculated
        error_occurred(error_message: str): Emitted when an error occurs
    """

    checksum_calculated = pyqtSignal(str, str)
    error_occurred = pyqtSignal(str)

    def __init__(self, file_path: Path):
        """Initialize the checksum worker.

        Args:
            file_path: Path to the file for checksum calculation
        """
        super().__init__()
        self.file_path = file_path
        self.hash_types = ["MD5", "SHA256"]

    def run(self) -> None:
        """Calculate checksums for different hash algorithms."""
        try:
            for hash_type in self.hash_types:
                hash_obj = getattr(hashlib, hash_type.lower())()
                with open(self.file_path, "rb") as f:
                    for chunk in iter(lambda: f.read(4096), b""):
                        hash_obj.update(chunk)

                hash_value = hash_obj.hexdigest()
                self.checksum_calculated.emit(hash_type, hash_value)

        except Exception as e:
            logger.error(f"Error calculating checksum for {self.file_path}: {e}")
            self.error_occurred.emit(f"Error calculating checksum: {str(e)}")


class PropertiesDialog(QDialog):
    """Modal dialog for displaying detailed file properties.

    Shows file information including path, size, modification times,
    permissions, and checksums. Checksums are calculated on-demand.
    """

    def __init__(self, file_path: Union[str, Path], parent=None):
        """Initialize the properties dialog.

        Args:
            file_path: Path to the file whose properties to display
            parent: Parent widget
        """
        super().__init__(parent)
        self.file_path = Path(file_path).resolve()

        if not self.file_path.exists():
            raise FileSearchError(f"File does not exist: {file_path}")

        self.setWindowTitle("Properties")
        self.setModal(True)
        self.resize(400, 600)

        self.checksum_worker = None
        self.setup_ui()
        self.load_file_info()

    def setup_ui(self) -> None:
        """Setup the user interface components."""
        # Main layout
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Scroll area for long content
        scroll_area = QScrollArea()
        scroll_widget = QWidget()
        self.form_layout = QFormLayout()
        scroll_widget.setLayout(self.form_layout)
        scroll_area.setWidget(scroll_widget)
        scroll_area.setWidgetResizable(True)
        layout.addWidget(scroll_area)

        # Buttons at bottom
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        # Calculate Checksums button
        self.checksum_button = QPushButton("Calculate Checksums")
        self.checksum_button.clicked.connect(self.calculate_checksums)
        button_layout.addWidget(self.checksum_button)

        # Close button
        self.close_button = QPushButton("Close")
        self.close_button.clicked.connect(self.accept)
        button_layout.addWidget(self.close_button)

        layout.addLayout(button_layout)

        # Progress bar for checksum calculation (initially hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

    def load_file_info(self) -> None:
        """Load and display basic file information."""
        try:
            stat = self.file_path.stat()

            # File name and path
            self._add_info_row("Name:", self.file_path.name)
            self._add_info_row("Path:", str(self.file_path))

            # Size information
            size_bytes = stat.st_size
            size_display = self._format_file_size(size_bytes)
            self._add_info_row("Size:", size_display)
            self._add_info_row("Size (bytes):", f"{size_bytes:,}")

            # Type (extension or "directory")
            if self.file_path.is_dir():
                file_type = "Directory"
            else:
                ext = self.file_path.suffix
                file_type = f"{ext.upper()} file" if ext else "File"
            self._add_info_row("Type:", file_type)

            # Modification dates
            modified_time = datetime.fromtimestamp(stat.st_mtime)
            self._add_info_row("Modified:", modified_time.strftime("%Y-%m-%d %H:%M:%S"))

            created_time = None
            if hasattr(stat, "st_birthtime") and stat.st_birthtime:
                # macOS/Linux
                created_time = datetime.fromtimestamp(stat.st_birthtime)
            elif hasattr(stat, "st_ctime") and stat.st_ctime:
                # Windows (creation time) or fallback
                # Note: ctime on Windows is creation time, on Unix it's change time
                created_time = datetime.fromtimestamp(stat.st_ctime)

            if created_time:
                self._add_info_row(
                    "Created:", created_time.strftime("%Y-%m-%d %H:%M:%S")
                )

            # Access time
            access_time = datetime.fromtimestamp(stat.st_atime)
            self._add_info_row(
                "Last accessed:", access_time.strftime("%Y-%m-%d %H:%M:%S")
            )

            # Permissions
            perm_str = self._get_permissions_string()
            self._add_info_row("Permissions:", perm_str)

            # Checksum placeholders (calculated on demand)
            self.md5_label = self._add_info_row("MD5 checksum:", "Not calculated")
            self.sha256_label = self._add_info_row("SHA256 checksum:", "Not calculated")

        except Exception as e:
            logger.error(f"Error loading file info for {self.file_path}: {e}")
            self._add_info_row("Error:", f"Could not read file information: {str(e)}")

    def _add_info_row(self, label_text: str, value_text: str) -> QLabel:
        """Add a label-value pair to the form layout.

        Args:
            label_text: The label text
            value_text: The value text

        Returns:
            The value label widget (for later updating if needed)
        """
        label = QLabel(f"<b>{label_text}</b>")
        value_label = QLabel(value_text)
        value_label.setWordWrap(True)
        value_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )

        self.form_layout.addRow(label, value_label)
        return value_label

    def _format_file_size(self, size_bytes: int) -> str:
        """Format file size in human-readable format."""
        if size_bytes == 0:
            return "0 bytes"

        size_names = ["bytes", "KB", "MB", "GB", "TB"]
        i = int(math.floor(math.log(size_bytes, 1024)))
        p = math.pow(1024, i)
        s = round(size_bytes / p, 2)
        return f"{s} {size_names[i]}"

    def _get_permissions_string(self) -> str:
        """Get a string representation of file permissions."""
        try:
            # Get basic permission info
            stat = self.file_path.stat()
            perm_mode = stat.st_mode

            # Get permissions as octal string
            octal_perms = oct(perm_mode)[-3:]

            # Convert to rwx format
            perm_str = ""
            for i, char in enumerate(octal_perms):
                flags = int(char)
                r = "r" if flags & 4 else "-"
                w = "w" if flags & 2 else "-"
                x = "x" if flags & 1 else "-"
                perm_str += r + w + x

                # Add separators between user/group/other
                if i < 2:
                    perm_str += " "

            return perm_str

        except Exception as e:
            logger.warning(f"Could not read permissions for {self.file_path}: {e}")
            return "Unknown"

    def calculate_checksums(self) -> None:
        """Calculate file checksums in a background thread."""
        if self.checksum_worker and self.checksum_worker.isRunning():
            return  # Already calculating

        # Update UI
        self.checksum_button.setEnabled(False)
        self.checksum_button.setText("Calculating...")
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        self.md5_label.setText("Calculating...")
        self.sha256_label.setText("Calculating...")

        # Start background calculation
        self.checksum_worker = ChecksumWorker(self.file_path)
        self.checksum_worker.checksum_calculated.connect(self.on_checksum_calculated)
        self.checksum_worker.error_occurred.connect(self.on_checksum_error)
        self.checksum_worker.finished.connect(self.on_checksum_finished)
        self.checksum_worker.start()

    def on_checksum_calculated(self, hash_type: str, hash_value: str) -> None:
        """Handle checksum calculation completion."""
        if hash_type == "MD5":
            self.md5_label.setText(hash_value.upper())
        elif hash_type == "SHA256":
            self.sha256_label.setText(hash_value.upper())

        logger.debug(f"Calculated {hash_type} checksum for {self.file_path}")

    def on_checksum_error(self, error_message: str) -> None:
        """Handle checksum calculation error."""
        self.md5_label.setText(f"Error: {error_message}")
        self.sha256_label.setText(f"Error: {error_message}")
        logger.error(
            f"Checksum calculation error for {self.file_path}: {error_message}"
        )

    def on_checksum_finished(self) -> None:
        """Handle checksum calculation thread completion."""
        self.checksum_button.setEnabled(True)
        self.checksum_button.setText("Calculate Checksums")
        self.progress_bar.setVisible(False)

        if self.checksum_worker:
            self.checksum_worker = None
