from datetime import datetime
from typing import List, Optional

from loguru import logger
from PyQt6.QtCore import (
    QAbstractListModel,
    QModelIndex,
    QPoint,
    QRect,
    QSize,
    Qt,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QAbstractTextDocumentLayout,
    QColor,
    QCursor,
    QFont,
    QKeyEvent,
    QStandardItem,
    QStandardItemModel,
    QTextDocument,
)
from PyQt6.QtWidgets import QAbstractItemView, QListView, QStyle, QStyledItemDelegate

from ..core.exceptions import FileSearchError
from ..core.file_utils import rename_file
from ..core.sort_engine import SortCriteria, SortEngine
from ..models.search_result import SearchResult
from ..utils.highlight_engine import HighlightEngine


class ResultsModel(QAbstractListModel):
    """Custom model for results list with virtual scrolling support"""

    error_occurred = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._results = []
        self._displayed_count = 0
        self._batch_size = 100  # Load 100 items at a time for smooth scrolling
        self._current_sort_criteria = None
        self._current_query = ""

    def rowCount(self, parent=QModelIndex()):
        return self._displayed_count

    def data(self, index, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or index.row() >= self._displayed_count:
            return None

        result = self._results[index.row()]

        if role == Qt.ItemDataRole.DisplayRole:
            return result.get_display_name()
        elif role == Qt.ItemDataRole.UserRole:
            return result
        elif role == Qt.ItemDataRole.ToolTipRole:
            return (
                f"Filename: {result.path.name}\n"
                f"Path: {result.path}\n"
                f"Size: {result.get_display_size()}\n"
                f"Modified: {result.get_display_date()}"
            )

        return None

    def flags(self, index):
        """Return item flags"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(self, index, value, role=Qt.ItemDataRole.EditRole):
        """Handle data updates (renaming)"""
        if not index.isValid() or role != Qt.ItemDataRole.EditRole:
            return False

        result = self._results[index.row()]
        new_name = str(value)

        # Skip if name hasn't changed
        if new_name == result.path.name:
            return False

        try:
            new_path = rename_file(result.path, new_name)

            # Update result object
            result.path = new_path

            # Emit data changed signal
            self.dataChanged.emit(
                index,
                index,
                [
                    Qt.ItemDataRole.DisplayRole,
                    Qt.ItemDataRole.UserRole,
                    Qt.ItemDataRole.ToolTipRole,
                ],
            )
            return True

        except Exception as e:
            logger.error(f"Rename failed: {e}")
            self.error_occurred.emit(str(e))
            return False

    def canFetchMore(self, parent=QModelIndex()):
        """Check if more results can be fetched for virtual scrolling"""
        if parent.isValid():
            return False
        return self._displayed_count < len(self._results)

    def fetchMore(self, parent=QModelIndex()):
        """Fetch more results for virtual scrolling"""
        if parent.isValid():
            return

        remaining = len(self._results) - self._displayed_count
        items_to_fetch = min(self._batch_size, remaining)

        if items_to_fetch <= 0:
            return

        self.beginInsertRows(
            QModelIndex(),
            self._displayed_count,
            self._displayed_count + items_to_fetch - 1,
        )
        self._displayed_count += items_to_fetch
        self.endInsertRows()

    def add_result(self, result):
        """Add a single result to the model"""
        self.beginInsertRows(QModelIndex(), len(self._results), len(self._results))
        self._results.append(result)

        # Auto-fetch if we're still in initial loading phase
        if (
            self._displayed_count < len(self._results)
            and len(self._results) <= self._displayed_count + self._batch_size
        ):
            self._displayed_count += 1

        self.endInsertRows()

    def remove_result(self, result):
        """Remove a single result from the model"""
        try:
            idx = self._results.index(result)
            self.beginRemoveRows(QModelIndex(), idx, idx)
            self._results.pop(idx)
            if idx < self._displayed_count:
                self._displayed_count -= 1
            self.endRemoveRows()
            return True
        except ValueError:
            return False

    def clear(self):
        """Clear all results from the model"""
        self.beginResetModel()
        self._results.clear()
        self._displayed_count = 0
        self.endResetModel()

    def set_results(self, results):
        """Set all results at once (used for initial load or refresh)"""
        self.beginResetModel()
        self._results = results
        self._displayed_count = min(self._batch_size, len(self._results))
        self.endResetModel()

    def get_all_results(self):
        """Get all results (including those not yet displayed)"""
        return self._results

    def sort_results(self, criteria: SortCriteria, query: str = ""):
        """Sort results using the specified criteria.

        AC3: Selection and scroll position should be preserved.
        For now, we sort all results and reset display count.

        Args:
            criteria: SortCriteria enum value
            query: Search query (required for relevance sorting)
        """
        if not self._results:
            return

        # Store current state
        self._current_sort_criteria = criteria
        self._current_query = query

        # Sort all results
        sorted_results = SortEngine.sort(self._results, criteria, query)

        # Reset model with sorted results
        self.set_results(sorted_results)

    def get_current_sort_criteria(self) -> Optional[SortCriteria]:
        """Get the currently applied sort criteria"""
        return self._current_sort_criteria

    def get_sort_query(self) -> str:
        """Get the query used for relevance sorting"""
        return self._current_query


class ResultsItemDelegate(QStyledItemDelegate):
    """Custom delegate for rendering search result items with highlighting support"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.bold_font = QFont()
        self.bold_font.setBold(True)
        self.normal_font = QFont()
        self.small_font = QFont()
        self.small_font.setPointSize(11)
        self.icon_cache = {}
        self.highlight_engine = HighlightEngine()
        self.current_query = None
        self.highlight_color = "#FFFF99"  # Default yellow highlight
        self.highlight_enabled = True
        self.highlight_style = "background"  # background, outline, or underline

    def get_file_type_icon(self, path):
        """Get file type icon based on extension with caching"""
        if path.is_dir():
            return self.icon_cache.setdefault("dir", "📁")
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
        return self.icon_cache.setdefault(ext, icon_map.get(ext, "📄"))

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

        # Filename (bold left-aligned, with highlighting)
        filename_rect = QRect(
            icon_rect.right() + 5, rect.top(), rect.width() - icon_size - 10 - 100, 20
        )
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
            # Draw normally (without highlighting)
            painter.setFont(self.bold_font)
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
        """Draw text with highlighted matching portions"""
        if not text or not query or not self.highlight_enabled:
            # No highlighting, just draw the text normally
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text
            )
            return

        matches = self.highlight_engine.find_matches(text, query, case_sensitive=False)

        if not matches:
            # No matches, draw text normally
            painter.drawText(
                rect, Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop, text
            )
            return

        # For performance with many results, we'll use a simple approach:
        # Draw normal text with bold segments for matches
        # This avoids QTextDocument overhead for each item

        painter.save()

        name_without_ext, ext = self.highlight_engine._split_filename_and_ext(text)

        # Calculate positions for manual text drawing
        x = rect.left()
        y = rect.top()

        last_end = 0

        for start, end in matches:
            # Draw non-matching text before this match
            if start > last_end:
                normal_text = name_without_ext[last_end:start]
                painter.setFont(self.normal_font)
                painter.setPen(QColor(0, 0, 0))
                painter.drawText(x, y, normal_text)
                x += painter.fontMetrics().horizontalAdvance(normal_text)

            # Draw highlighted matching text
            match_text = name_without_ext[start:end]
            painter.setFont(self.bold_font)

            # Calculate dimensions
            bw = painter.fontMetrics().horizontalAdvance(match_text)
            bh = painter.fontMetrics().height()

            # Apply highlight style
            if self.highlight_style == "background":
                # Draw background highlight
                painter.fillRect(x, y - bh + 2, bw, bh, QColor(self.highlight_color))
                painter.setPen(QColor(0, 0, 0))
            elif self.highlight_style == "outline":
                # Draw outline rectangle
                pen = painter.pen()
                pen.setColor(QColor(self.highlight_color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawRect(x, y - bh, bw, bh)
                painter.setPen(QColor(0, 0, 0))  # Reset to black for text
            elif self.highlight_style == "underline":
                # Draw underline
                pen = painter.pen()
                pen.setColor(QColor(self.highlight_color))
                pen.setWidth(2)
                painter.setPen(pen)
                painter.drawLine(x, y, x + bw, y)  # Line at baseline
                painter.setPen(QColor(0, 0, 0))  # Reset to black for text

            painter.drawText(x, y, match_text)
            x += bw

            last_end = end

        # Draw remaining non-matching text
        if last_end < len(name_without_ext):
            remaining_text = name_without_ext[last_end:]
            painter.setFont(self.normal_font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x, y, remaining_text)
            x += painter.fontMetrics().horizontalAdvance(remaining_text)

        # Draw extension
        if ext:
            painter.setFont(self.normal_font)
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(x, y, ext)

        painter.restore()


class ResultsView(QListView):
    """Results view component for displaying search results"""

    # Custom signal for file opening requests
    file_open_requested = pyqtSignal(object)  # SearchResult
    # Custom signal for context menu requests
    context_menu_requested = pyqtSignal(QPoint)  # Global position of the right-click

    def __init__(self, parent=None):
        super().__init__(parent)

        # Model - use ResultsModel for virtual scrolling
        self._empty_model = QStandardItemModel()  # For empty states
        self._results_model = None
        self.setModel(self._empty_model)

        # Enable custom context menu policy
        self.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.customContextMenuRequested.connect(self._on_custom_context_menu_requested)

        # Delegate
        self.setItemDelegate(ResultsItemDelegate(self))

        # View settings
        self.setMinimumHeight(200)  # Minimum 10 items at ~20px each
        self.setVerticalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setHorizontalScrollMode(QAbstractItemView.ScrollMode.ScrollPerPixel)
        self.setSelectionMode(QAbstractItemView.SelectionMode.SingleSelection)
        self.setAlternatingRowColors(False)
        self.setUniformItemSizes(True)  # Optimize for virtual scrolling

        # Enable smooth scrolling
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Enable virtual scrolling
        self.setUniformItemSizes(True)

        # Keyboard navigation
        self.setFocusPolicy(Qt.FocusPolicy.StrongFocus)

        # Double-click handling
        self.doubleClicked.connect(self._on_double_clicked)

        # Mouse tracking for hover cursor changes
        self.setMouseTracking(True)

        # Search state tracking
        self._is_searching = False

        # Empty state - don't show initially

        # Store reference to delegate for highlighting
        self._delegate = self.itemDelegate()

    def _on_custom_context_menu_requested(self, pos: QPoint) -> None:
        """
        Handles the custom context menu request by emitting a signal with the global position.
        """
        # Map the local position to global coordinates for the main window
        global_pos = self.mapToGlobal(pos)
        self.context_menu_requested.emit(global_pos)

    def set_query(self, query: str):
        """Set the current search query for highlighting"""
        if self._delegate:
            self._delegate.set_query(query)
        # Trigger repaint to apply highlighting
        self.viewport().update()

    def set_highlight_enabled(self, enabled: bool):
        """Enable or disable highlighting"""
        if self._delegate:
            self._delegate.set_highlight_enabled(enabled)
        self.viewport().update()

    def set_highlight_color(self, color: str):
        """Set the highlight color (HTML hex code like #FFFF99)"""
        if self._delegate:
            self._delegate.set_highlight_color(color)
        self.viewport().update()

    def set_highlight_style(self, style: str):
        """Set the highlight style ('background', 'outline', or 'underline')"""
        if self._delegate:
            self._delegate.set_highlight_style(style)
        self.viewport().update()

    def _show_empty_state(self, message: str):
        """Show empty state message"""
        self._empty_model.clear()
        item = QStandardItem(message)
        item.setData(None, Qt.ItemDataRole.UserRole)  # No SearchResult
        self._empty_model.appendRow(item)

    def set_results(self, results: List[SearchResult]):
        """Set search results to display"""
        if results:
            if not self._results_model:
                self._results_model = ResultsModel()
                # Connect error signal
                self._results_model.error_occurred.connect(self._on_model_error)
            self._results_model.set_results(results)
            self.setModel(self._results_model)
            # Auto-scroll to first result when search completes
            self.scrollToTop()
            # Search is complete, enable double-click
            self.set_search_active(False)
        else:
            self.setModel(self._empty_model)
            self._show_empty_state("No files found")
            # Search is complete, enable double-click
            self.set_search_active(False)

    def _on_model_error(self, message: str):
        """Handle errors from the model"""
        from PyQt6.QtWidgets import QMessageBox

        QMessageBox.critical(self, "Error", message)

    def clear_results(self):
        """Clear all results"""
        self.setModel(self._empty_model)
        self._empty_model.clear()
        self._show_empty_state("Enter a search term to begin")
        if self._results_model:
            self._results_model.clear()
        # Reset search state
        self.set_search_active(False)

    def set_searching_state(self):
        """Set searching state with spinner message"""
        self.setModel(self._empty_model)
        self._empty_model.clear()
        self._show_empty_state("Searching...")
        # Update search state
        self._is_searching = True
        self.setCursor(QCursor(Qt.CursorShape.BusyCursor))

    def add_result(self, result: SearchResult):
        """Add a single result to the view"""
        if not self._results_model:
            self._results_model = ResultsModel()
            self._results_model.error_occurred.connect(self._on_model_error)
            self.setModel(self._results_model)
            # Clear the searching state when first result arrives
            self.set_search_active(False)
            # Force viewport update to show the new model
            self.viewport().update()
        # Maintain scroll position when adding results
        scroll_bar = self.verticalScrollBar()
        vertical_scroll = scroll_bar.value() if scroll_bar else 0
        self._results_model.add_result(result)
        if scroll_bar:
            scroll_bar.setValue(vertical_scroll)

    def get_selected_result(self) -> Optional[SearchResult]:
        """Get the currently selected SearchResult"""
        indexes = self.selectedIndexes()
        if indexes:
            model = self.model()
            if model == self._empty_model:
                return indexes[0].data(Qt.ItemDataRole.UserRole)
            else:
                return indexes[0].data(Qt.ItemDataRole.UserRole)
        return None

    def apply_sorting(self, criteria: SortCriteria):
        """Apply sorting to current results

        AC6: Sort results using specified criteria

        Args:
            criteria: SortCriteria enum value
        """
        if not self._results_model or not self._results_model.get_all_results():
            return

        # Get current query from delegate for relevance sorting
        query = getattr(self._delegate, "current_query", "") if self._delegate else ""

        # Apply sorting
        self._results_model.sort_results(criteria, query)

    def get_current_sort_criteria(self) -> Optional[SortCriteria]:
        """Get the current sort criteria"""
        if self._results_model:
            return self._results_model.get_current_sort_criteria()
        return None

    def keyPressEvent(self, e) -> None:
        """Handle keyboard navigation for results list"""
        if e is None:
            super().keyPressEvent(e)
            return

        # Handle keyboard shortcuts for sorting (Ctrl+1..5 for criteria, Ctrl+R to reverse)
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            if e.key() == Qt.Key.Key_1:
                self.apply_sorting(SortCriteria.NAME_ASC)
                return
            elif e.key() == Qt.Key.Key_2:
                self.apply_sorting(SortCriteria.SIZE_ASC)
                return
            elif e.key() == Qt.Key.Key_3:
                self.apply_sorting(SortCriteria.DATE_DESC)
                return
            elif e.key() == Qt.Key.Key_4:
                self.apply_sorting(SortCriteria.TYPE_ASC)
                return
            elif e.key() == Qt.Key.Key_5:
                self.apply_sorting(SortCriteria.RELEVANCE_DESC)
                return
            elif e.key() == Qt.Key.Key_R:
                # Reverse current sort
                current = self.get_current_sort_criteria()
                if current == SortCriteria.NAME_ASC:
                    self.apply_sorting(SortCriteria.NAME_DESC)
                elif current == SortCriteria.NAME_DESC:
                    self.apply_sorting(SortCriteria.NAME_ASC)
                elif current == SortCriteria.SIZE_ASC:
                    self.apply_sorting(SortCriteria.SIZE_DESC)
                elif current == SortCriteria.SIZE_DESC:
                    self.apply_sorting(SortCriteria.SIZE_ASC)
                elif current == SortCriteria.DATE_ASC:
                    self.apply_sorting(SortCriteria.DATE_DESC)
                elif current == SortCriteria.DATE_DESC:
                    self.apply_sorting(SortCriteria.DATE_ASC)
                return

        if not self._results_model:
            super().keyPressEvent(e)
            return

        current_index = self.currentIndex()
        if not current_index.isValid():
            super().keyPressEvent(e)
            return

        key = e.key()
        model = self._results_model

        if key == Qt.Key.Key_Up:
            # Move selection up
            if current_index.row() > 0:
                new_index = model.index(current_index.row() - 1, 0)
                self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_Down:
            # Move selection down
            if current_index.row() < model.rowCount() - 1:
                new_index = model.index(current_index.row() + 1, 0)
                self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_Home:
            # Move to first item
            if model.rowCount() > 0:
                new_index = model.index(0, 0)
                self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_End:
            # Move to last item
            if model.rowCount() > 0:
                new_index = model.index(model.rowCount() - 1, 0)
                self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_PageUp:
            # Move up by viewport height
            visible_count = self.height() // self.sizeHint().height()
            new_row = max(0, current_index.row() - visible_count)
            new_index = model.index(new_row, 0)
            self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_PageDown:
            # Move down by viewport height
            visible_count = self.height() // self.sizeHint().height()
            new_row = min(model.rowCount() - 1, current_index.row() + visible_count)
            new_index = model.index(new_row, 0)
            self.setCurrentIndex(new_index)
        elif key == Qt.Key.Key_Return or key == Qt.Key.Key_Enter:
            # Activate selected item (double-click equivalent)
            self.doubleClicked.emit(current_index)
        elif key == Qt.Key.Key_Menu:
            # Trigger context menu at current selection
            rect = self.visualRect(current_index)
            center = rect.center()
            global_pos = self.mapToGlobal(center)
            self.context_menu_requested.emit(global_pos)
        else:
            # Let parent handle other keys
            super().keyPressEvent(e)
            return

    def _on_double_clicked(self, index: QModelIndex) -> None:
        """Handle double-click events on results.

        Args:
            index: Model index of the double-clicked item
        """
        if not index.isValid():
            return

        # Don't allow opening during search
        if self._is_searching:
            return

        # Get the SearchResult object
        model = self.model()
        if model == self._empty_model:
            result = index.data(Qt.ItemDataRole.UserRole)
        else:
            result = index.data(Qt.ItemDataRole.UserRole)

        if result:
            # Emit signal for main window to handle
            self.file_open_requested.emit(result)

            # Add visual feedback - brief highlight flash
            self._add_highlight_flash(index)

    def _add_highlight_flash(self, index: QModelIndex) -> None:
        """Add a brief highlight flash effect to the double-clicked item.

        Args:
            index: Model index of the item to highlight
        """
        # Store original selection
        original_selection = self.selectedIndexes()

        # Temporarily select and highlight the item
        self.setCurrentIndex(index)

        # Force a repaint to show the highlight
        self.viewport().update()

        # Use QTimer to restore original selection after brief delay
        from PyQt6.QtCore import QTimer

        QTimer.singleShot(150, lambda: self._restore_selection(original_selection))

    def _restore_selection(self, original_selection) -> None:
        """Restore the original selection after highlight flash.

        Args:
            original_selection: List of originally selected indexes
        """
        if original_selection:
            self.setCurrentIndex(original_selection[0])
        else:
            self.clearSelection()

    def mouseMoveEvent(self, e) -> None:
        """Handle mouse move events for cursor changes.

        Args:
            e: Mouse move event
        """
        # Check if mouse is over an item
        index = self.indexAt(e.pos())
        if index.isValid():
            # Change to pointer hand cursor over items
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            # Restore default cursor
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        super().mouseMoveEvent(e)

    def set_search_active(self, is_searching: bool) -> None:
        """Set the searching state to control double-click availability.

        Args:
            is_searching: True if search is in progress, False otherwise
        """
        self._is_searching = is_searching

        # Update cursor based on search state
        if is_searching:
            self.setCursor(QCursor(Qt.CursorShape.BusyCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

    def is_search_active(self) -> bool:
        """Check if a search is currently in progress.

        Returns:
            True if searching, False otherwise
        """
        return self._is_searching
