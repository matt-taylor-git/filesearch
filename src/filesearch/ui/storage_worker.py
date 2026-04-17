"""Background worker for storage analysis."""

from __future__ import annotations

from pathlib import Path

from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal

from filesearch.core.exceptions import SearchError
from filesearch.core.storage_analyzer import StorageAnalyzer


class StorageWorker(QThread):
    """Run storage analysis without blocking the UI."""

    progress_update = pyqtSignal(str, int, int)
    analysis_complete = pyqtSignal(object)
    analysis_error = pyqtSignal(str)
    analysis_cancelled = pyqtSignal()

    def __init__(self, analyzer: StorageAnalyzer, root_path: Path) -> None:
        super().__init__()
        self.analyzer = analyzer
        self.root_path = root_path

    def run(self) -> None:
        """Run the analysis and emit Qt signals."""
        try:
            logger.info(f"Starting storage worker for {self.root_path}")
            result = self.analyzer.analyze(self.root_path, self._on_progress)
            if self.analyzer.is_cancelled():
                self.analysis_cancelled.emit()
                return
            self.analysis_complete.emit(result)
        except SearchError as exc:
            if self.analyzer.is_cancelled() or "cancelled" in str(exc).lower():
                self.analysis_cancelled.emit()
                return
            logger.error(f"Storage analysis error: {exc}")
            self.analysis_error.emit(str(exc))
        except Exception as exc:
            logger.error(f"Unexpected storage analysis error: {exc}")
            self.analysis_error.emit(f"Unexpected error: {exc}")

    def stop(self) -> None:
        """Request cancellation."""
        self.analyzer.cancel()
        logger.info("Storage worker stop requested")

    def _on_progress(
        self, current_path: str, item_count: int, skipped_count: int
    ) -> None:
        """Forward progress notifications to the UI thread."""
        self.progress_update.emit(current_path, item_count, skipped_count)
