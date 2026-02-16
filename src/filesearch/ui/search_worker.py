"""Background search worker thread."""

from pathlib import Path

from loguru import logger
from PyQt6.QtCore import QThread, pyqtSignal

from filesearch.core.exceptions import FileSearchError
from filesearch.core.search_engine import FileSearchEngine


class SearchWorker(QThread):
    """Worker thread for performing file searches in the background.

    This class handles search operations in a separate thread to keep the UI
    responsive during searches.

    Signals:
        result_found(Path, int): Emitted when a matching file is found
        progress_update(int, str, int): Emitted for search progress updates
        search_complete(int, int): Emitted when search is complete
        error_occurred(str, int): Emitted when an error occurs
        search_stopped(int, int): Emitted when search is stopped
    """

    result_found = pyqtSignal(dict, int)  # result_dict, result_number
    progress_update = pyqtSignal(
        int, str, int
    )  # progress_percent, current_dir, files_found
    search_complete = pyqtSignal(int, int)  # total_files, total_dirs
    error_occurred = pyqtSignal(str, int)  # error_message, error_code
    search_stopped = pyqtSignal(int, int)  # files_found, dirs_searched

    def __init__(
        self,
        search_engine: FileSearchEngine,
        directory: Path,
        query: str,
        progress_callback=None,
    ):
        """Initialize the search worker.

        Args:
            search_engine: FileSearchEngine instance
            directory: Directory to search in
            query: Search pattern
            progress_callback: Callback for progress updates
        """
        super().__init__()
        self.search_engine = search_engine
        self.directory = directory
        self.query = query
        self.progress_callback = progress_callback
        self._is_running = False

        logger.debug(f"SearchWorker initialized for {directory} with query '{query}'")

    def run(self) -> None:
        """Execute the search operation."""
        self._is_running = True
        files_found = 0
        dirs_searched = 0

        try:
            logger.info(f"Starting search in {self.directory} for '{self.query}'")

            # Perform the search (includes plugin results)
            for result in self.search_engine.search(self.directory, self.query):
                if not self._is_running:
                    break

                files_found += 1
                self.result_found.emit(result, files_found)

                # Update progress periodically
                if files_found % 10 == 0:
                    self.progress_update.emit(50, str(self.directory), files_found)

            if self._is_running:
                self.search_complete.emit(files_found, dirs_searched)
                logger.info(f"Search completed: {files_found} files found")
            else:
                self.search_stopped.emit(files_found, dirs_searched)
                logger.info(f"Search stopped: {files_found} files found")

        except FileSearchError as e:
            logger.error(f"Search error: {e}")
            self.error_occurred.emit(str(e), 1)
        except Exception as e:
            logger.error(f"Unexpected search error: {e}")
            self.error_occurred.emit(f"Unexpected error: {e}", 2)

    def stop(self) -> None:
        """Stop the search operation."""
        self._is_running = False
        self.search_engine.cancel()
        logger.info("SearchWorker stop requested")
