"""Sidebar widget for the 3-panel file search layout.

Provides location shortcuts, file type filters, recent search tags,
and disk storage indicator.
"""

import shutil
from pathlib import Path
from typing import Dict, List, Optional, Set

import qtawesome as qta
from loguru import logger
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLabel,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QVBoxLayout,
    QWidget,
)

from filesearch.ui.theme import Colors, Fonts, Spacing

# File type extension mapping for client-side filtering
FILE_TYPE_EXTENSIONS: Dict[str, Set[str]] = {
    "Documents": {
        ".txt", ".pdf", ".doc", ".docx", ".odt", ".rtf", ".xls", ".xlsx",
        ".ppt", ".pptx", ".csv", ".md", ".tex", ".epub",
    },
    "Images": {
        ".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".ico",
        ".tiff", ".tif", ".raw", ".psd",
    },
    "Videos": {
        ".mp4", ".avi", ".mkv", ".mov", ".wmv", ".flv", ".webm", ".m4v",
        ".mpg", ".mpeg",
    },
    "Audio": {
        ".mp3", ".wav", ".flac", ".aac", ".ogg", ".wma", ".m4a", ".opus",
    },
    "Archives": {
        ".zip", ".rar", ".7z", ".tar", ".gz", ".bz2", ".xz", ".iso",
    },
    "Code": {
        ".py", ".js", ".ts", ".jsx", ".tsx", ".html", ".css", ".scss",
        ".java", ".c", ".cpp", ".h", ".hpp", ".cs", ".go", ".rs", ".rb",
        ".php", ".swift", ".kt", ".sh", ".bat", ".ps1", ".sql", ".json",
        ".xml", ".yaml", ".yml", ".toml", ".ini", ".cfg",
    },
}

# Tag badge color rotation
TAG_COLORS = [
    Colors.TAG_BLUE,
    Colors.TAG_GREEN,
    Colors.TAG_PURPLE,
    Colors.TAG_YELLOW,
    Colors.TAG_RED,
]


class SidebarWidget(QWidget):
    """Sidebar with locations, file type filters, tags, and storage bar.

    Signals:
        directory_selected(Path): Emitted when a location is clicked.
        file_type_filter_changed(list): Emitted when file type toggles change.
        tag_clicked(str): Emitted when a recent search tag is clicked.
    """

    directory_selected = pyqtSignal(Path)
    file_type_filter_changed = pyqtSignal(list)
    tag_clicked = pyqtSignal(str)
    browse_requested = pyqtSignal()

    def __init__(self, parent: Optional[QWidget] = None) -> None:
        super().__init__(parent)
        self.setObjectName("sidebarWidget")
        self.setFixedWidth(240)
        self.setSizePolicy(QSizePolicy.Policy.Fixed, QSizePolicy.Policy.Expanding)

        self._location_buttons: List[QPushButton] = []
        self._active_location: Optional[QPushButton] = None
        self._filter_buttons: Dict[str, QPushButton] = {}
        self._active_filters: Set[str] = set()
        self._tag_buttons: List[QPushButton] = []
        self._custom_location_button: Optional[QPushButton] = None
        self._browse_button: Optional[QPushButton] = None
        self._location_map: Dict[str, Path] = {}

        self._setup_ui()
        logger.debug("SidebarWidget initialized")

    def _setup_ui(self) -> None:
        """Build the sidebar layout."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)
        outer.setSpacing(0)

        # --- Scroll area wrapping all content ---
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QScrollArea.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # --- App title ---
        title_row = QHBoxLayout()
        title_row.setSpacing(8)
        title_icon = QLabel()
        title_icon.setPixmap(
            qta.icon("mdi6.folder-search", color=Colors.PRIMARY).pixmap(22, 22)
        )
        title_icon.setFixedSize(22, 22)
        title_label = QLabel("File Search")
        title_label.setProperty("class", "sidebar-title")
        title_row.addWidget(title_icon)
        title_row.addWidget(title_label)
        title_row.addStretch()
        layout.addLayout(title_row)
        layout.addSpacing(16)

        # --- LOCATIONS ---
        layout.addWidget(self._section_header("LOCATIONS"))
        layout.addSpacing(4)

        home = Path.home()
        locations = [
            ("Home", home, "mdi6.home", Colors.PRIMARY),
            ("Documents", home / "Documents", "mdi6.file-document", Colors.TEXT_SECONDARY),
            ("Desktop", home / "Desktop", "mdi6.monitor", Colors.TEXT_SECONDARY),
            ("Downloads", home / "Downloads", "mdi6.download", Colors.TEXT_SECONDARY),
            ("Pictures", home / "Pictures", "mdi6.image", Colors.TEXT_SECONDARY),
            ("Videos", home / "Videos", "mdi6.video", Colors.TEXT_SECONDARY),
        ]
        self._location_map = {label: path for label, path, _, _ in locations}

        for label, path, icon_name, icon_color in locations:
            btn = self._location_button(label, path, icon_name, icon_color)
            layout.addWidget(btn)
            self._location_buttons.append(btn)

        self._custom_location_button = self._location_button(
            "Custom Folder",
            home,
            "mdi6.folder",
            Colors.FILE_FOLDER,
        )
        self._custom_location_button.setVisible(False)
        layout.addWidget(self._custom_location_button)

        self._browse_button = QPushButton(
            qta.icon("mdi6.folder-open", color=Colors.TEXT_SECONDARY),
            "  Choose Folder...",
        )
        self._browse_button.setProperty("class", "sidebar-item")
        self._browse_button.setProperty("active", "false")
        self._browse_button.setCursor(Qt.CursorShape.PointingHandCursor)
        self._browse_button.setIconSize(
            self._browse_button.iconSize().__class__(18, 18)
        )
        self._browse_button.clicked.connect(
            lambda checked=False: self.browse_requested.emit()
        )
        layout.addWidget(self._browse_button)

        layout.addSpacing(16)

        # --- FILE TYPES ---
        layout.addWidget(self._section_header("FILE TYPES"))
        layout.addSpacing(4)

        chip_specs = [
            ("Documents", "mdi6.file-document", Colors.FILE_DOC),
            ("Images", "mdi6.image", Colors.FILE_IMAGE),
            ("Videos", "mdi6.video", Colors.FILE_VIDEO),
            ("Audio", "mdi6.music", Colors.FILE_AUDIO),
            ("Archives", "mdi6.zip-box", Colors.FILE_ARCHIVE),
            ("Code", "mdi6.code-tags", Colors.FILE_CODE),
        ]

        # Two chips per row
        row: Optional[QHBoxLayout] = None
        for i, (name, icon_name, color) in enumerate(chip_specs):
            if i % 2 == 0:
                row = QHBoxLayout()
                row.setSpacing(6)
                layout.addLayout(row)
            chip = self._filter_chip(name, icon_name, color)
            self._filter_buttons[name] = chip
            if row is not None:
                row.addWidget(chip)
        # Fill last row if odd count
        if len(chip_specs) % 2 != 0 and row is not None:
            row.addStretch()

        layout.addSpacing(16)

        # --- TAGS (recent searches) ---
        layout.addWidget(self._section_header("TAGS"))
        layout.addSpacing(4)

        self._tags_container = QVBoxLayout()
        self._tags_container.setSpacing(4)
        layout.addLayout(self._tags_container)

        # Stretch to push storage to bottom
        layout.addStretch()

        # --- Storage ---
        layout.addSpacing(8)
        layout.addWidget(self._section_header("STORAGE"))
        layout.addSpacing(4)
        self._storage_bar = QProgressBar()
        self._storage_bar.setProperty("class", "storage-bar")
        self._storage_bar.setTextVisible(False)
        self._storage_bar.setFixedHeight(6)
        layout.addWidget(self._storage_bar)

        self._storage_label = QLabel()
        self._storage_label.setProperty("class", "storage-text")
        layout.addWidget(self._storage_label)

        self._update_storage()

        scroll.setWidget(container)
        outer.addWidget(scroll)

    # --- Factory helpers ---

    def _section_header(self, text: str) -> QLabel:
        lbl = QLabel(text)
        lbl.setProperty("class", "sidebar-section")
        return lbl

    def _location_button(
        self, label: str, path: Path, icon_name: str, icon_color: str
    ) -> QPushButton:
        icon = qta.icon(icon_name, color=icon_color)
        btn = QPushButton(icon, f"  {label}")
        btn.setProperty("class", "sidebar-item")
        btn.setProperty("active", "false")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setIconSize(btn.iconSize().__class__(18, 18))
        btn.clicked.connect(
            lambda checked, p=path, b=btn: self._on_location_clicked(p, b)
        )
        return btn

    def _filter_chip(self, name: str, icon_name: str, color: str) -> QPushButton:
        icon = qta.icon(icon_name, color=color)
        btn = QPushButton(icon, name)
        btn.setProperty("class", "filter-chip")
        btn.setProperty("active", "false")
        btn.setCursor(Qt.CursorShape.PointingHandCursor)
        btn.setCheckable(True)
        btn.setIconSize(btn.iconSize().__class__(14, 14))
        btn.clicked.connect(
            lambda checked, n=name: self._on_filter_toggled(n, checked)
        )
        return btn

    # --- Slots ---

    def _on_location_clicked(self, path: Path, button: QPushButton) -> None:
        self._set_active_button(button)
        self.directory_selected.emit(path)
        logger.debug(f"Sidebar location selected: {path}")

    def _on_filter_toggled(self, name: str, checked: bool) -> None:
        btn = self._filter_buttons.get(name)
        if btn:
            btn.setProperty("active", "true" if checked else "false")
            style = btn.style()
            if style:
                style.unpolish(btn)
                style.polish(btn)

        if checked:
            self._active_filters.add(name)
        else:
            self._active_filters.discard(name)

        # Collect all extensions from active filters
        extensions: List[str] = []
        for f in self._active_filters:
            extensions.extend(FILE_TYPE_EXTENSIONS.get(f, set()))

        self.file_type_filter_changed.emit(extensions)
        logger.debug(f"File type filter changed: {self._active_filters}")

    # --- Public methods ---

    def set_active_location_by_path(self, path: Path) -> None:
        """Highlight the sidebar location matching *path*."""
        self._set_active_button(None)

        for btn in self._location_buttons:
            label = btn.text().strip()
            if self._location_map.get(label) == path:
                self._set_active_button(btn)
                return

        if self._custom_location_button and self._custom_location_button.isVisible():
            custom_path = self._custom_location_button.property("path")
            if custom_path and Path(custom_path) == path:
                self._set_active_button(self._custom_location_button)

    def set_custom_location(self, path: Optional[Path]) -> None:
        """Show or hide the custom folder location row."""
        if self._custom_location_button is None:
            return

        if not path:
            if self._active_location is self._custom_location_button:
                self._set_active_button(None)
            self._custom_location_button.setVisible(False)
            self._custom_location_button.setToolTip("")
            self._custom_location_button.setProperty("path", "")
            return

        folder_name = path.name or str(path)
        self._custom_location_button.setText(f"  {folder_name}")
        self._custom_location_button.setToolTip(str(path))
        self._custom_location_button.setProperty("path", str(path))
        try:
            self._custom_location_button.clicked.disconnect()
        except TypeError:
            pass
        self._custom_location_button.clicked.connect(
            lambda checked=False, p=path, b=self._custom_location_button: (
                self._on_location_clicked(p, b)
            )
        )
        self._custom_location_button.setVisible(True)

    def get_custom_location(self) -> Optional[Path]:
        """Return the currently displayed custom folder, if any."""
        if not self._custom_location_button:
            return None

        custom_path = self._custom_location_button.property("path")
        if not custom_path:
            return None

        return Path(custom_path)

    def set_tags(self, searches: List[str]) -> None:
        """Update the recent search tags."""
        # Clear existing
        for btn in self._tag_buttons:
            btn.deleteLater()
        self._tag_buttons.clear()

        # Wrap tags in a flow-like layout (row of 2-3)
        row: Optional[QHBoxLayout] = None
        for i, text in enumerate(searches[:8]):
            if i % 3 == 0:
                row = QHBoxLayout()
                row.setSpacing(4)
                self._tags_container.addLayout(row)

            color = TAG_COLORS[i % len(TAG_COLORS)]
            btn = QPushButton(text)
            btn.setProperty("class", "tag-badge")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.setStyleSheet(f"background-color: {color};")
            btn.setMaximumWidth(100)
            btn.clicked.connect(lambda checked, t=text: self.tag_clicked.emit(t))
            self._tag_buttons.append(btn)
            if row is not None:
                row.addWidget(btn)

        # Pad last row
        if row is not None and len(searches[:8]) % 3 != 0:
            row.addStretch()

    def _update_storage(self) -> None:
        """Update the disk usage indicator."""
        try:
            usage = shutil.disk_usage(Path.home())
            used_pct = int((usage.used / usage.total) * 100)
            self._storage_bar.setRange(0, 100)
            self._storage_bar.setValue(used_pct)

            used_gb = usage.used / (1024 ** 3)
            total_gb = usage.total / (1024 ** 3)
            self._storage_label.setText(
                f"{used_gb:.1f} GB of {total_gb:.1f} GB used"
            )
        except Exception as e:
            logger.warning(f"Could not read disk usage: {e}")
            self._storage_bar.setRange(0, 100)
            self._storage_bar.setValue(0)
            self._storage_label.setText("Storage info unavailable")

    def get_active_extensions(self) -> List[str]:
        """Return list of active filter extensions (empty = no filter)."""
        extensions: List[str] = []
        for f in self._active_filters:
            extensions.extend(FILE_TYPE_EXTENSIONS.get(f, set()))
        return extensions

    def _set_active_button(self, button: Optional[QPushButton]) -> None:
        """Update sidebar active styling so only one location is highlighted."""
        all_buttons = list(self._location_buttons)
        if self._custom_location_button is not None:
            all_buttons.append(self._custom_location_button)

        for candidate in all_buttons:
            candidate.setProperty("active", "true" if candidate is button else "false")
            style = candidate.style()
            if style:
                style.unpolish(candidate)
                style.polish(candidate)

        self._active_location = button
