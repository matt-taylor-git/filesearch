from datetime import datetime
from typing import List, Optional

from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QAbstractItemView, QListView, QStyle, QStyledItemDelegate

from ..models.search_result import SearchResult


class ResultsItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering search result items"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.normal_font = QFont()
        self.small_font = QFont()
        self.small_font.setPointSize(11)

    def get_file_type_icon(self, path):
        """Get file type icon based on extension"""
        if path.is_dir():
            return "📁"
        ext = path.suffix.lower()
        icon_map = {
            ".txt": "📄",
            ".pdf": "📕",
            ".doc": "📄",
            ".docx": "📄",
            ".jpg": "📷",
            ".jpeg": "📷",
            ".png": "🖼️",
            ".gif": "📷",
            ".mp4": "📽️",
            ".avi": "📽️",
            ".mp3": "🎵",
            ".wav": "🎵",
            ".zip": "📦",
            ".rar": "📦",
            ".exe": "⚙️",
            ".py": "🐍",
            ".js": "📜",
            ".html": "🌐",
            ".css": "🎨",
        }
        return icon_map.get(ext, "📄")

    def paint(self, painter, option, index):
        """Custom paint method for result items"""
        if painter is None:
            return
        painter.save()

        # Get the SearchResult from the model
        result = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            super().paint(painter, option, index)
            painter.restore()
            return

        # Draw background
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, option.palette.highlight())
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(240, 240, 240))
            # Light gray hover
        # Margins
        margin = 5
        rect = option.rect.adjusted(margin, margin, -margin, -margin)

        # Icon
        icon_size = 16
        icon_rect = QRect(rect.left(), rect.top() + 2, icon_size, icon_size)
        icon_text = self.get_file_type_icon(result.path)
        painter.setFont(self.normal_font)
        painter.drawText(icon_rect, Qt.AlignmentFlag.AlignCenter, icon_text)

        # Filename (bold, left-aligned)
        filename_rect = QRect(
            icon_rect.right() + 5, rect.top(), rect.width() - icon_size - 10 - 100, 20
        )
        painter.setFont(self.bold_font)
        filename = result.get_display_name()
        if len(filename) > 80:
            filename = filename[:77] + "..."
        painter.drawText(
            filename_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            filename,
        )

        # Path (small font, below filename)
        path_rect = QRect(
            filename_rect.left(), filename_rect.bottom(), filename_rect.width(), 15
        )
        painter.setFont(self.small_font)
        path = result.get_display_path()
        if len(path) > 80:
            path = "..." + path[-77:]  # Truncate from left
        painter.setPen(QColor(128, 128, 128))  # Gray
        painter.drawText(
            path_rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, path
        )

        # Size (right-aligned)
        size_rect = QRect(rect.right() - 90, rect.top(), 85, 20)
        painter.setFont(self.normal_font)
        painter.setPen(QColor(0, 0, 0))  # Black
        size_text = result.get_display_size()
        painter.drawText(
            size_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            size_text,
        )

        # Modified date (if space, below size)
        if rect.height() > 40:
            date_rect = QRect(
                size_rect.left(), size_rect.bottom(), size_rect.width(), 15
            )
            painter.setFont(self.small_font)
            painter.setPen(QColor(128, 128, 128))
            try:
                date_text = datetime.fromtimestamp(result.modified).strftime(
                    "%b %d, %Y"
                )
            except Exception:
                date_text = "Unknown"
            painter.drawText(
                date_rect,
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
                date_text,
            )
        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        """Return the size hint for items"""
        return QSize(400, 50)  # Minimum height for comfortable display


class ResultsView(QListView):
    """Results view component for displaying search results"""

    def __init__(self, parent=None):
        super().__init__(parent)

        # Model
        self._model = QStandardItemModel()
        self.setModel(self._model)

        # Delegate
        self.setItemDelegate(ResultsItemDelegate(self))

        # View settings
        self.setMinimumHeight(200)  # Minimum 10 items at ~20px each
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)

        # Enable smooth scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Empty state - don't show initially

    def _show_empty_state(self, message: str):
        """Show empty state message"""
        self._model.clear()
        item = QStandardItem(message)
        item.setData(None, Qt.ItemDataRole.UserRole)  # No SearchResult
        self._model.appendRow(item)

    def set_results(self, results: List[SearchResult]):
        """Set the search results to display"""
        self._model.clear()

        if not results:
            self._show_empty_state("No files found")
            return

        for result in results:
            item = QStandardItem(result.get_display_name())
            item.setData(result, Qt.ItemDataRole.UserRole)
            self._model.appendRow(item)

    def clear_results(self):
        """Clear all results"""
        self._model.clear()
        self._show_empty_state("Enter a search term to begin")

    def add_result(self, result: SearchResult):
        """Add a single result to the view"""
        item = QStandardItem(result.get_display_name())
        item.setData(result, Qt.ItemDataRole.UserRole)
        # Set tooltips
        item.setToolTip(
            f"Filename: {result.path.name}\n"
            f"Path: {result.path}\n"
            f"Size: {result.get_display_size()}\n"
            f"Modified: {result.get_display_date()}"
        )
        self._model.appendRow(item)

    def get_selected_result(self) -> Optional[SearchResult]:
        """Get the currently selected SearchResult"""
        indexes = self.selectedIndexes()
        if indexes:
            return indexes[0].data(Qt.ItemDataRole.UserRole)
        return None
