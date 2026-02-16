"""Custom delegate for rendering search result items with highlighting."""

from datetime import datetime
from typing import Dict

import qtawesome as qta
from PyQt6.QtCore import QModelIndex, QRect, QSize, Qt
from PyQt6.QtGui import QColor, QFont, QPixmap
from PyQt6.QtWidgets import QStyle, QStyledItemDelegate

from filesearch.models.search_result import SearchResult
from filesearch.utils.highlight_engine import HighlightEngine


def _get_file_icon_info(path) -> tuple:
    """Return (qta icon name, color hex) for a file path."""
    from filesearch.ui.theme import Colors as C

    if path.is_dir():
        return "mdi6.folder", C.FILE_FOLDER

    ext = path.suffix.lower()
    _map = {
        ".pdf": ("mdi6.file-pdf-box", C.FILE_PDF),
        ".doc": ("mdi6.file-word", C.FILE_DOC),
        ".docx": ("mdi6.file-word", C.FILE_DOC),
        ".xls": ("mdi6.file-excel", C.FILE_DOC),
        ".xlsx": ("mdi6.file-excel", C.FILE_DOC),
        ".ppt": ("mdi6.file-powerpoint", C.FILE_DOC),
        ".pptx": ("mdi6.file-powerpoint", C.FILE_DOC),
        ".txt": ("mdi6.file-document", C.FILE_DOC),
        ".md": ("mdi6.file-document", C.FILE_DOC),
        ".rtf": ("mdi6.file-document", C.FILE_DOC),
        ".csv": ("mdi6.file-delimited", C.FILE_DOC),
        ".jpg": ("mdi6.file-image", C.FILE_IMAGE),
        ".jpeg": ("mdi6.file-image", C.FILE_IMAGE),
        ".png": ("mdi6.file-image", C.FILE_IMAGE),
        ".gif": ("mdi6.file-image", C.FILE_IMAGE),
        ".bmp": ("mdi6.file-image", C.FILE_IMAGE),
        ".svg": ("mdi6.file-image", C.FILE_IMAGE),
        ".webp": ("mdi6.file-image", C.FILE_IMAGE),
        ".mp4": ("mdi6.file-video", C.FILE_VIDEO),
        ".avi": ("mdi6.file-video", C.FILE_VIDEO),
        ".mkv": ("mdi6.file-video", C.FILE_VIDEO),
        ".mov": ("mdi6.file-video", C.FILE_VIDEO),
        ".wmv": ("mdi6.file-video", C.FILE_VIDEO),
        ".mp3": ("mdi6.file-music", C.FILE_AUDIO),
        ".wav": ("mdi6.file-music", C.FILE_AUDIO),
        ".flac": ("mdi6.file-music", C.FILE_AUDIO),
        ".aac": ("mdi6.file-music", C.FILE_AUDIO),
        ".ogg": ("mdi6.file-music", C.FILE_AUDIO),
        ".zip": ("mdi6.zip-box", C.FILE_ARCHIVE),
        ".rar": ("mdi6.zip-box", C.FILE_ARCHIVE),
        ".7z": ("mdi6.zip-box", C.FILE_ARCHIVE),
        ".tar": ("mdi6.zip-box", C.FILE_ARCHIVE),
        ".gz": ("mdi6.zip-box", C.FILE_ARCHIVE),
        ".py": ("mdi6.language-python", C.FILE_CODE),
        ".js": ("mdi6.language-javascript", C.FILE_CODE),
        ".ts": ("mdi6.language-typescript", C.FILE_CODE),
        ".html": ("mdi6.language-html5", C.FILE_CODE),
        ".css": ("mdi6.language-css3", C.FILE_CODE),
        ".java": ("mdi6.language-java", C.FILE_CODE),
        ".cpp": ("mdi6.language-cpp", C.FILE_CODE),
        ".c": ("mdi6.language-c", C.FILE_CODE),
        ".go": ("mdi6.language-go", C.FILE_CODE),
        ".rs": ("mdi6.language-rust", C.FILE_CODE),
        ".rb": ("mdi6.language-ruby", C.FILE_CODE),
        ".json": ("mdi6.code-json", C.FILE_CODE),
        ".xml": ("mdi6.file-xml-box", C.FILE_CODE),
        ".yaml": ("mdi6.file-code", C.FILE_CODE),
        ".yml": ("mdi6.file-code", C.FILE_CODE),
        ".sh": ("mdi6.console", C.FILE_CODE),
        ".bat": ("mdi6.console", C.FILE_CODE),
        ".exe": ("mdi6.application", "#858BA0"),
    }
    return _map.get(ext, ("mdi6.file", C.TEXT_SECONDARY))


# Pixmap cache for file-type icons (key = "icon_name:color")
_icon_pixmap_cache: Dict[str, QPixmap] = {}


def _get_file_icon_pixmap(path, size: int = 20) -> QPixmap:
    """Return a cached QPixmap for the file type."""
    icon_name, color = _get_file_icon_info(path)
    key = f"{icon_name}:{color}:{size}"
    if key not in _icon_pixmap_cache:
        _icon_pixmap_cache[key] = qta.icon(icon_name, color=color).pixmap(size, size)
    return _icon_pixmap_cache[key]


class ResultsItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering search result items with highlighting support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        from filesearch.ui.theme import Colors, Fonts, Spacing

        # Theme-aware fonts
        self.filename_font = QFont("Segoe UI", Fonts.SIZE_BASE)
        self.filename_font.setWeight(QFont.Weight.DemiBold)
        self.path_font = QFont("Segoe UI", Fonts.SIZE_XS)
        self.size_font = QFont("Segoe UI", Fonts.SIZE_XS)
        self.size_font.setWeight(QFont.Weight.Medium)
        self.date_font = QFont("Segoe UI", Fonts.SIZE_XS)

        self.icon_cache = {}
        self.highlight_engine = HighlightEngine()
        self.current_query = None
        self.highlight_color = Colors.HIGHLIGHT_BG
        self.highlight_text_color = Colors.HIGHLIGHT_TEXT
        self.highlight_enabled = True
        self.highlight_style = "background"  # background, outline, or underline

        # Cache theme colors
        self._colors = Colors
        self._spacing = Spacing

    def get_file_type_icon(self, path):
        """Get file type icon based on extension with caching (legacy fallback)"""
        if path.is_dir():
            return self.icon_cache.setdefault("dir", "\U0001f4c1")
        ext = path.suffix.lower()
        icon_map = {
            ".txt": "\U0001f4c4",
            ".pdf": "\U0001f4d5",
            ".doc": "\U0001f4c4",
            ".docx": "\U0001f4c4",
            ".jpg": "\U0001f4f7",
            ".jpeg": "\U0001f4f7",
            ".png": "\U0001f5bc\ufe0f",
            ".gif": "\U0001f4f7",
            ".mp4": "\U0001f4fd\ufe0f",
            ".avi": "\U0001f4fd\ufe0f",
            ".mp3": "\U0001f3b5",
            ".wav": "\U0001f3b5",
            ".zip": "\U0001f4e6",
            ".rar": "\U0001f4e6",
            ".exe": "\u2699\ufe0f",
            ".py": "\U0001f40d",
            ".js": "\U0001f4dc",
            ".html": "\U0001f310",
            ".css": "\U0001f3a8",
        }
        return self.icon_cache.setdefault(ext, icon_map.get(ext, "\U0001f4c4"))

    def paint(self, painter, option, index):
        """Custom paint method for result items with polished theme styling"""
        if painter is None:
            return
        painter.save()

        # Get the SearchResult from the model
        result = index.data(Qt.ItemDataRole.UserRole)
        if not isinstance(result, SearchResult):
            super().paint(painter, option, index)
            painter.restore()
            return

        C = self._colors
        pad = self._spacing.PADDING_ITEM

        # Draw background based on state
        if option.state & QStyle.StateFlag.State_Selected:
            painter.fillRect(option.rect, QColor(C.ITEM_SELECTED_BG))
        elif option.state & QStyle.StateFlag.State_MouseOver:
            painter.fillRect(option.rect, QColor(C.ITEM_HOVER_BG))

        # Draw subtle separator line at bottom
        sep_y = option.rect.bottom()
        painter.setPen(QColor(C.ITEM_SEPARATOR))
        painter.drawLine(
            option.rect.left() + pad, sep_y, option.rect.right() - pad, sep_y
        )

        # Content area with padding
        rect = option.rect.adjusted(pad, pad - 2, -pad, -pad)

        # --- Icon (QtAwesome pixmap) ---
        icon_size = 20
        icon_pixmap = _get_file_icon_pixmap(result.path, icon_size)
        icon_x = rect.left()
        icon_y = rect.top() + 2
        painter.drawPixmap(icon_x, icon_y, icon_pixmap)

        content_left = icon_x + icon_size + 8

        # === Right side: Size pill and date ===
        size_text = result.get_display_size()
        painter.setFont(self.size_font)
        size_fm = painter.fontMetrics()
        pill_text_width = size_fm.horizontalAdvance(size_text)
        pill_h = size_fm.height() + 6
        pill_w = pill_text_width + self._spacing.PADDING_PILL * 2
        pill_x = rect.right() - pill_w
        pill_y = rect.top() + 2

        # Draw pill background with subtle border
        pill_rect = QRect(pill_x, pill_y, pill_w, pill_h)
        painter.setPen(QColor(C.BORDER_DEFAULT))
        painter.setBrush(QColor(C.SIZE_PILL_BG))
        painter.drawRoundedRect(pill_rect, 5, 5)

        # Draw pill text
        painter.setPen(QColor(C.TEXT_SECONDARY))
        painter.setFont(self.size_font)
        painter.drawText(
            pill_rect,
            Qt.AlignmentFlag.AlignCenter,
            size_text,
        )

        # Date (right-aligned below pill)
        try:
            date_text = datetime.fromtimestamp(result.modified).strftime("%b %d, %Y")
        except Exception:
            date_text = "Unknown"

        painter.setFont(self.date_font)
        date_fm = painter.fontMetrics()
        date_w = date_fm.horizontalAdvance(date_text)
        date_rect = QRect(
            rect.right() - date_w,
            pill_y + pill_h + 4,
            date_w,
            date_fm.height(),
        )
        painter.setPen(QColor(C.TEXT_TERTIARY))
        painter.drawText(
            date_rect,
            Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignTop,
            date_text,
        )

        # === Left side: Filename and path ===
        filename_width = pill_x - content_left - 12

        # Filename
        filename_rect = QRect(content_left, rect.top(), filename_width, 20)
        filename = result.get_display_name()
        if len(filename) > 80:
            filename = filename[:77] + "..."

        # Use highlighting if query is set
        if (
            self.current_query
            and self.highlight_enabled
            and self.highlight_engine.has_matches(filename, self.current_query)
        ):
            self._draw_highlighted_text(
                painter, filename_rect, filename, self.current_query
            )
        else:
            painter.setFont(self.filename_font)
            painter.setPen(QColor(C.TEXT_PRIMARY))
            painter.drawText(
                filename_rect,
                Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
                filename,
            )

        # Path (below filename)
        path_rect = QRect(
            content_left, filename_rect.bottom() + 2, filename_width, 16
        )
        painter.setFont(self.path_font)
        path = result.get_display_path()
        if len(path) > 80:
            path = "..." + path[-77:]
        painter.setPen(QColor(C.TEXT_TERTIARY))
        painter.drawText(
            path_rect,
            Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop,
            path,
        )

        painter.restore()

    def sizeHint(self, option, index: QModelIndex) -> QSize:
        """Return the size hint for items"""
        return QSize(400, 64)  # Spacious items with room for pill and separator

    def set_query(self, query: str):
        """Set the current search query for highlighting"""
        self.current_query = query
        self.highlight_engine.clear_cache()

    def set_highlight_enabled(self, enabled: bool):
        """Enable or disable highlighting"""
        self.highlight_enabled = enabled

    def set_highlight_color(self, color: str):
        """Set the highlight color (HTML color code)"""
        self.highlight_color = color

    def set_highlight_style(self, style: str):
        """Set the highlight style ('background', 'outline', or 'underline')"""
        self.highlight_style = style

    def _draw_highlighted_text(self, painter, rect, text: str, query: str):
        """Draw text with highlighted matching portions using theme colors"""
        if not text or not query or not self.highlight_enabled:
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text
            )
            return

        matches = self.highlight_engine.find_matches(
            text, query, case_sensitive=False
        )

        if not matches:
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text
            )
            return

        painter.save()

        C = self._colors
        name_without_ext, ext = self.highlight_engine._split_filename_and_ext(text)

        x = rect.left()
        y = rect.top()

        last_end = 0

        for start, end in matches:
            # Draw non-matching text before this match
            if start > last_end:
                normal_text = name_without_ext[last_end:start]
                painter.setFont(self.filename_font)
                painter.setPen(QColor(C.TEXT_PRIMARY))
                painter.drawText(x, y, normal_text)
                x += painter.fontMetrics().horizontalAdvance(normal_text)

            # Draw highlighted matching text
            match_text = name_without_ext[start:end]
            painter.setFont(self.filename_font)

            bw = painter.fontMetrics().horizontalAdvance(match_text)
            bh = painter.fontMetrics().height()

            if self.highlight_style == "background":
                # Rounded rect highlight with warm amber
                highlight_rect = QRect(x - 1, y - bh + 2, bw + 2, bh)
                painter.setPen(Qt.PenStyle.NoPen)
                painter.setBrush(QColor(self.highlight_color))
                painter.drawRoundedRect(highlight_rect, 3, 3)
                painter.setPen(QColor(self.highlight_text_color))
            elif self.highlight_style == "outline":
                pen = painter.pen()
                pen.setColor(QColor(self.highlight_color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRoundedRect(x, y - bh, bw, bh, 3, 3)
                painter.setPen(QColor(C.TEXT_PRIMARY))
            elif self.highlight_style == "underline":
                pen = painter.pen()
                pen.setColor(QColor(self.highlight_color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(x, y, x + bw, y)
                painter.setPen(QColor(C.TEXT_PRIMARY))

            painter.drawText(x, y, match_text)
            x += bw

            last_end = end

        # Draw remaining non-matching text
        if last_end < len(name_without_ext):
            remaining_text = name_without_ext[last_end:]
            painter.setFont(self.filename_font)
            painter.setPen(QColor(C.TEXT_PRIMARY))
            painter.drawText(x, y, remaining_text)
            x += painter.fontMetrics().horizontalAdvance(remaining_text)

        # Draw extension
        if ext:
            painter.setFont(self.filename_font)
            painter.setPen(QColor(C.TEXT_PRIMARY))
            painter.drawText(x, y, ext)

        painter.restore()
