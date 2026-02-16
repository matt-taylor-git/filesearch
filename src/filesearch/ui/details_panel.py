"""Details panel widget for the 3-panel file search layout.

Shows file preview icon, metadata, and action buttons for the currently
selected search result.  Hidden by default; appears when a result is selected.
"""

from datetime import datetime
from pathlib import Path
from typing import Optional

import qtawesome as qta
from loguru import logger
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QToolButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.models.search_result import SearchResult
from filesearch.ui.theme import Colors, Fonts, Spacing


def _get_file_type_icon_info(path: Path) -> tuple:
    """Return (qta icon name, color) for a given file path."""
    if path.is_dir():
        return "mdi6.folder", Colors.FILE_FOLDER

    ext = path.suffix.lower()
    mapping = {
        ".pdf": ("mdi6.file-pdf-box", Colors.FILE_PDF),
        ".doc": ("mdi6.file-word", Colors.FILE_DOC),
        ".docx": ("mdi6.file-word", Colors.FILE_DOC),
        ".jpg": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".jpeg": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".png": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".gif": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".bmp": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".svg": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".webp": ("mdi6.file-image", Colors.FILE_IMAGE),
        ".mp4": ("mdi6.file-video", Colors.FILE_VIDEO),
        ".avi": ("mdi6.file-video", Colors.FILE_VIDEO),
        ".mkv": ("mdi6.file-video", Colors.FILE_VIDEO),
        ".mov": ("mdi6.file-video", Colors.FILE_VIDEO),
        ".mp3": ("mdi6.file-music", Colors.FILE_AUDIO),
        ".wav": ("mdi6.file-music", Colors.FILE_AUDIO),
        ".flac": ("mdi6.file-music", Colors.FILE_AUDIO),
        ".aac": ("mdi6.file-music", Colors.FILE_AUDIO),
        ".ogg": ("mdi6.file-music", Colors.FILE_AUDIO),
        ".py": ("mdi6.code-tags", Colors.FILE_CODE),
        ".js": ("mdi6.code-tags", Colors.FILE_CODE),
        ".ts": ("mdi6.code-tags", Colors.FILE_CODE),
        ".html": ("mdi6.code-tags", Colors.FILE_CODE),
        ".css": ("mdi6.code-tags", Colors.FILE_CODE),
        ".java": ("mdi6.code-tags", Colors.FILE_CODE),
        ".cpp": ("mdi6.code-tags", Colors.FILE_CODE),
        ".c": ("mdi6.code-tags", Colors.FILE_CODE),
        ".go": ("mdi6.code-tags", Colors.FILE_CODE),
        ".rs": ("mdi6.code-tags", Colors.FILE_CODE),
        ".zip": ("mdi6.zip-box", Colors.FILE_ARCHIVE),
        ".rar": ("mdi6.zip-box", Colors.FILE_ARCHIVE),
        ".7z": ("mdi6.zip-box", Colors.FILE_ARCHIVE),
        ".tar": ("mdi6.zip-box", Colors.FILE_ARCHIVE),
        ".gz": ("mdi6.zip-box", Colors.FILE_ARCHIVE),
    }
    return mapping.get(ext, ("mdi6.file", Colors.TEXT_SECONDARY))


def _get_file_type_label(path: Path) -> str:
    """Return a human-readable type label for a file."""
    if path.is_dir():
        return "Folder"
    ext = path.suffix.lower()
    labels = {
        ".pdf": "PDF Document",
        ".doc": "Word Document",
        ".docx": "Word Document",
        ".txt": "Text File",
        ".md": "Markdown File",
        ".jpg": "JPEG Image",
        ".jpeg": "JPEG Image",
        ".png": "PNG Image",
        ".gif": "GIF Image",
        ".svg": "SVG Image",
        ".mp4": "MP4 Video",
        ".avi": "AVI Video",
        ".mkv": "MKV Video",
        ".mp3": "MP3 Audio",
        ".wav": "WAV Audio",
        ".flac": "FLAC Audio",
        ".py": "Python File",
        ".js": "JavaScript File",
        ".ts": "TypeScript File",
        ".html": "HTML File",
        ".css": "CSS File",
        ".zip": "ZIP Archive",
        ".rar": "RAR Archive",
    }
    return labels.get(ext, f"{ext.upper().lstrip('.')} File" if ext else "File")


class DetailsPanelWidget(QWidget):
    """Right-side details panel showing info about the selected result.

    Signals:
        open_requested(object): Open the file.
        open_folder_requested(object): Open containing folder.
        copy_path_requested(object): Copy file path.
        delete_requested(object): Move file to trash.
        panel_close_requested(): Hide the panel.
    """

    open_requested = pyqtSignal(object)
    open_folder_requested = pyqtSignal(object)
    copy_path_requested = pyqtSignal(object)
    delete_requested = pyqtSignal(object)
    panel_close_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("detailsPanel")
        self.setMinimumWidth(0)  # Allow splitter to collapse to 0
        self.setSizePolicy(QSizePolicy.Policy.Preferred, QSizePolicy.Policy.Expanding)

        self._current_result: Optional[SearchResult] = None
        self._setup_ui()

        logger.debug("DetailsPanelWidget initialized")

    def _setup_ui(self) -> None:
        """Build the panel layout."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(16, 12, 16, 16)
        outer.setSpacing(0)

        # --- Header row ---
        header_row = QHBoxLayout()
        header_label = QLabel("DETAILS")
        header_label.setProperty("class", "details-header")
        header_row.addWidget(header_label)
        header_row.addStretch()

        self._close_btn = QToolButton()
        self._close_btn.setIcon(
            qta.icon("mdi6.close", color=Colors.TEXT_TERTIARY)
        )
        self._close_btn.setProperty("class", "details-close")
        self._close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._close_btn.setFixedSize(24, 24)
        self._close_btn.clicked.connect(self.panel_close_requested.emit)
        header_row.addWidget(self._close_btn)
        outer.addLayout(header_row)
        outer.addSpacing(16)

        # --- Scrollable content ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        content = QWidget()
        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # File icon (large)
        self._icon_label = QLabel()
        self._icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._icon_label.setFixedHeight(64)
        layout.addWidget(self._icon_label)

        # Filename
        self._filename_label = QLabel()
        self._filename_label.setProperty("class", "details-filename")
        self._filename_label.setWordWrap(True)
        self._filename_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._filename_label)

        # File info ("2.4 MB - PDF Document")
        self._fileinfo_label = QLabel()
        self._fileinfo_label.setProperty("class", "details-fileinfo")
        self._fileinfo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self._fileinfo_label)

        layout.addSpacing(8)

        # Open button (primary, full width)
        self._open_btn = QPushButton(
            qta.icon("mdi6.open-in-new", color="#FFFFFF"), "  Open"
        )
        self._open_btn.setProperty("class", "details-open")
        self._open_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_btn.clicked.connect(self._on_open)
        layout.addWidget(self._open_btn)

        # Action buttons row
        action_row = QHBoxLayout()
        action_row.setSpacing(8)

        self._open_folder_btn = QPushButton(
            qta.icon("mdi6.folder-open", color=Colors.TEXT_SECONDARY), " Folder"
        )
        self._open_folder_btn.setProperty("class", "details-action")
        self._open_folder_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._open_folder_btn.clicked.connect(self._on_open_folder)
        action_row.addWidget(self._open_folder_btn)

        self._copy_path_btn = QPushButton(
            qta.icon("mdi6.content-copy", color=Colors.TEXT_SECONDARY), " Copy Path"
        )
        self._copy_path_btn.setProperty("class", "details-action")
        self._copy_path_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._copy_path_btn.clicked.connect(self._on_copy_path)
        action_row.addWidget(self._copy_path_btn)

        layout.addLayout(action_row)

        layout.addSpacing(12)

        # --- Metadata ---
        self._meta_location_label = self._meta_pair(layout, "Location")
        self._meta_created_label = self._meta_pair(layout, "Created")
        self._meta_modified_label = self._meta_pair(layout, "Modified")
        self._meta_size_label = self._meta_pair(layout, "Size")

        layout.addStretch()

        # Trash button at bottom
        self._trash_btn = QPushButton(
            qta.icon("mdi6.trash-can", color=Colors.ERROR), " Move to Trash"
        )
        self._trash_btn.setProperty("class", "details-trash")
        self._trash_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self._trash_btn.clicked.connect(self._on_delete)
        layout.addWidget(self._trash_btn)

        scroll.setWidget(content)
        outer.addWidget(scroll)

    def _meta_pair(self, parent_layout: QVBoxLayout, label: str) -> QLabel:
        """Add a metadata label + value pair and return the value label."""
        lbl = QLabel(label)
        lbl.setProperty("class", "details-meta-label")
        parent_layout.addWidget(lbl)

        val = QLabel("—")
        val.setProperty("class", "details-meta-value")
        val.setWordWrap(True)
        parent_layout.addWidget(val)
        parent_layout.addSpacing(4)
        return val

    # --- Public API ---

    def show_result(self, result: SearchResult) -> None:
        """Populate the panel with details for *result* and show it."""
        self._current_result = result
        path = result.path

        # Icon
        icon_name, icon_color = _get_file_type_icon_info(path)
        self._icon_label.setPixmap(
            qta.icon(icon_name, color=icon_color).pixmap(48, 48)
        )

        # Filename
        self._filename_label.setText(path.name)

        # File info
        type_label = _get_file_type_label(path)
        size_str = result.get_display_size()
        self._fileinfo_label.setText(f"{size_str} — {type_label}")

        # Metadata
        self._meta_location_label.setText(str(path.parent))
        try:
            created = datetime.fromtimestamp(path.stat().st_ctime)
            self._meta_created_label.setText(created.strftime("%b %d, %Y %H:%M"))
        except Exception:
            self._meta_created_label.setText("—")

        try:
            modified = datetime.fromtimestamp(result.modified)
            self._meta_modified_label.setText(modified.strftime("%b %d, %Y %H:%M"))
        except Exception:
            self._meta_modified_label.setText("—")

        self._meta_size_label.setText(size_str)

        logger.debug(f"Details panel showing: {path.name}")

    def clear(self) -> None:
        """Clear panel content (splitter handles hiding via size)."""
        self._current_result = None

    # --- Slots ---

    def _on_open(self) -> None:
        if self._current_result:
            self.open_requested.emit(self._current_result)

    def _on_open_folder(self) -> None:
        if self._current_result:
            self.open_folder_requested.emit(self._current_result)

    def _on_copy_path(self) -> None:
        if self._current_result:
            self.copy_path_requested.emit(self._current_result)

    def _on_delete(self) -> None:
        if self._current_result:
            self.delete_requested.emit(self._current_result)
