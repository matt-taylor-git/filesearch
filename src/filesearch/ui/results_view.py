"""Results view component for displaying search results."""

from typing import List, Optional

from PyQt6.QtCore import QModelIndex, QPoint, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QStandardItem, QStandardItemModel
from PyQt6.QtWidgets import QAbstractItemView, QListView

from filesearch.core.sort_engine import SortCriteria
from filesearch.models.search_result import SearchResult
from filesearch.ui.results_delegate import ResultsItemDelegate
from filesearch.ui.results_model import ResultsModel  # noqa: F401 — re-exported


class ResultsView(QListView):
    """Results view component for displaying search results"""

    # Custom signal for file opening requests
    file_open_requested = pyqtSignal(object)  # SearchResult
    # Custom signal for folder opening requests (AC: Open Containing Folder)
    folder_open_requested = pyqtSignal(object)  # SearchResult
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

        # Disable double-click to edit, so double-click opens file
        self.setEditTriggers(QAbstractItemView.EditTrigger.EditKeyPressed)

        # Double-click handling
        self.doubleClicked.connect(self._on_double_clicked)

        # Mouse tracking for hover cursor changes
        self.setMouseTracking(True)

        # Search state tracking
        self._is_searching = False

        # Store reference to delegate for highlighting
        self._delegate = self.itemDelegate()

    def _on_custom_context_menu_requested(self, pos: QPoint) -> None:
        """Handles the custom context menu request by emitting a signal with the global
        position.
        """
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
        if self._results_model:
            self._results_model.clear()
        self.setModel(self._empty_model)
        self._empty_model.clear()
        self._show_empty_state("Searching...")
        # Update search state
        self._is_searching = True
        self.setCursor(QCursor(Qt.CursorShape.BusyCursor))

    def add_result(self, result: SearchResult):
        """Add a single result to the view"""
        if not self._results_model or self.model() == self._empty_model:
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

        # Handle keyboard shortcuts for sorting (Ctrl+1..5 for criteria, Ctrl+R to
        # reverse)
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

        # Handle Ctrl+Shift+O (Open Containing Folder)
        if e.modifiers() == (
            Qt.KeyboardModifier.ControlModifier | Qt.KeyboardModifier.ShiftModifier
        ):
            if e.key() == Qt.Key.Key_O:
                result = self.get_selected_result()
                if result:
                    self.folder_open_requested.emit(result)
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

    def mouseDoubleClickEvent(self, e) -> None:
        """Handle mouse double click events.

        Overridden to distinguish between clicking on filename (open file)
        and clicking on path (open containing folder).
        """
        if self._is_searching:
            return

        index = self.indexAt(e.pos())
        if index.isValid():
            rect = self.visualRect(index)
            relative_y = e.pos().y() - rect.y()

            if relative_y > 34:
                # Clicked on path area - open folder
                result = index.data(Qt.ItemDataRole.UserRole)
                if result:
                    self.folder_open_requested.emit(result)
                    self._add_highlight_flash(index)
            else:
                # Clicked on filename area - open file
                self.doubleClicked.emit(index)

            e.accept()
            return

        super().mouseDoubleClickEvent(e)

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

        result = index.data(Qt.ItemDataRole.UserRole)

        if result:
            self.file_open_requested.emit(result)
            self._add_highlight_flash(index)

    def _add_highlight_flash(self, index: QModelIndex) -> None:
        """Add a brief highlight flash effect to the double-clicked item.

        Args:
            index: Model index of the item to highlight
        """
        original_selection = self.selectedIndexes()
        self.setCurrentIndex(index)
        self.viewport().update()

        from PyQt6.QtCore import QTimer

        QTimer.singleShot(150, lambda: self._restore_selection(original_selection))

    def _restore_selection(self, original_selection) -> None:
        """Restore the original selection after highlight flash.

        Args:
            original_selection: List of originally selected indexes
        """
        try:
            if original_selection:
                self.setCurrentIndex(original_selection[0])
            else:
                self.clearSelection()
        except RuntimeError:
            # View might be deleted
            pass

    def mouseMoveEvent(self, e) -> None:
        """Handle mouse move events for cursor changes.

        Args:
            e: Mouse move event
        """
        index = self.indexAt(e.pos())
        if index.isValid():
            self.setCursor(QCursor(Qt.CursorShape.PointingHandCursor))
        else:
            self.setCursor(QCursor(Qt.CursorShape.ArrowCursor))

        super().mouseMoveEvent(e)

    def set_search_active(self, is_searching: bool) -> None:
        """Set the searching state to control double-click availability.

        Args:
            is_searching: True if search is in progress, False otherwise
        """
        self._is_searching = is_searching

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
