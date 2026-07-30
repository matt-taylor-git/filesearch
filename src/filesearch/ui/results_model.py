"""Results data model for the search results list view."""

from loguru import logger
from PyQt6.QtCore import QAbstractListModel, QModelIndex, QObject, Qt, pyqtSignal

from filesearch.core.file_utils import rename_file
from filesearch.core.sort_engine import SortCriteria, SortEngine
from filesearch.models.search_result import SearchResult


class ResultsModel(QAbstractListModel):
    """Custom model for results list with virtual scrolling support"""

    error_occurred = pyqtSignal(str)

    def __init__(self, parent: QObject | None = None) -> None:
        super().__init__(parent)
        self._all_results: list[SearchResult] = []  # Unfiltered master list
        self._results: list[SearchResult] = []  # Filtered view
        self._displayed_count = 0
        self._batch_size = 100  # Load 100 items at a time for smooth scrolling
        self._current_sort_criteria: SortCriteria | None = None
        self._current_query = ""
        self._extension_filter: list[str] = []  # Empty = show all

    def rowCount(
        self,
        parent: QModelIndex = QModelIndex(),  # noqa: B008 - Qt override signature.
    ) -> int:
        return self._displayed_count

    def data(
        self,
        index: QModelIndex,
        role: int = Qt.ItemDataRole.DisplayRole,
    ) -> object | None:
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

    def flags(self, index: QModelIndex) -> Qt.ItemFlag:
        """Return item flags"""
        if not index.isValid():
            return Qt.ItemFlag.NoItemFlags
        return super().flags(index) | Qt.ItemFlag.ItemIsEditable

    def setData(
        self,
        index: QModelIndex,
        value: object,
        role: int = Qt.ItemDataRole.EditRole,
    ) -> bool:
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

    def canFetchMore(
        self,
        parent: QModelIndex = QModelIndex(),  # noqa: B008 - Qt override signature.
    ) -> bool:
        """Check if more results can be fetched for virtual scrolling"""
        if parent.isValid():
            return False
        return self._displayed_count < len(self._results)

    def fetchMore(
        self,
        parent: QModelIndex = QModelIndex(),  # noqa: B008 - Qt override signature.
    ) -> None:
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

    def add_result(self, result: SearchResult) -> None:
        """Add a single result to the model"""
        self._all_results.append(result)

        # Check if result passes current filter
        if (
            self._extension_filter
            and result.path.suffix.lower() not in self._extension_filter
        ):
            return  # Filtered out, don't add to visible list

        self.beginInsertRows(QModelIndex(), len(self._results), len(self._results))
        self._results.append(result)

        # Auto-fetch if we're still in initial loading phase
        if (
            self._displayed_count < len(self._results)
            and len(self._results) <= self._displayed_count + self._batch_size
        ):
            self._displayed_count += 1

        self.endInsertRows()

    def remove_result(self, result: SearchResult) -> bool:
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

    def clear(self) -> None:
        """Clear all results from the model"""
        self.beginResetModel()
        self._all_results.clear()
        self._results.clear()
        self._displayed_count = 0
        self.endResetModel()

    def set_results(self, results: list[SearchResult]) -> None:
        """Set all results at once (used for initial load or refresh)"""
        self.beginResetModel()
        self._all_results = list(results)
        if self._extension_filter:
            self._results = [
                r
                for r in self._all_results
                if r.path.suffix.lower() in self._extension_filter
            ]
        else:
            self._results = list(self._all_results)
        self._displayed_count = min(self._batch_size, len(self._results))
        self.endResetModel()

    def get_all_results(self) -> list[SearchResult]:
        """Get all results (including those not yet displayed)"""
        return self._results

    def set_extension_filter(self, extensions: list[str]) -> None:
        """Filter visible results by file extension (client-side, no re-search).

        Args:
            extensions: List of extensions like ['.pdf', '.doc']. Empty = show all.
        """
        self._extension_filter = [e.lower() for e in extensions]
        self.beginResetModel()
        if self._extension_filter:
            self._results = [
                r
                for r in self._all_results
                if r.path.suffix.lower() in self._extension_filter
            ]
        else:
            self._results = list(self._all_results)
        self._displayed_count = min(self._batch_size, len(self._results))
        self.endResetModel()

    def sort_results(self, criteria: SortCriteria, query: str = "") -> None:
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

    def get_current_sort_criteria(self) -> SortCriteria | None:
        """Get the currently applied sort criteria"""
        return self._current_sort_criteria

    def get_sort_query(self) -> str:
        """Get the query used for relevance sorting"""
        return self._current_query
