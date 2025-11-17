"""Core search engine module for file searching functionality.

This module provides FileSearchEngine class that implements multi-threaded
file searching with partial matching, early termination, and generator-based
result streaming.
"""

import fnmatch
import os
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any, Dict, Generator, Optional, Set

from loguru import logger
from PyQt6.QtCore import QObject, pyqtSignal

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import SearchError


class FileSearchEngine(QObject):
    """Multi-threaded file search engine with generator-based result streaming.

    This class implements efficient file searching using concurrent directory
    traversal, partial matching with fnmatch patterns, and early termination
    when maximum results are reached.

    Attributes:
        max_workers (int): Maximum number of worker threads for parallel search
        max_results (int): Maximum number of results to return (0 = unlimited)
        _cancelled (bool): Flag to indicate if search should be cancelled
        _executor (Optional[ThreadPoolExecutor]): Thread pool for parallel execution
    """

    # Signals
    status_update = pyqtSignal(str, int)  # status, result_count
    results_count_update = pyqtSignal(int, int)  # current_count, total_so_far

    def __init__(
        self,
        max_workers: int = 4,
        max_results: int = 1000,
        config_manager: Optional[ConfigManager] = None,
        plugin_manager=None,
        progress_callback=None,
    ):
        """Initialize search engine.

        Args:
            max_workers: Maximum number of worker threads (default: 4)
            max_results: Maximum results to return, 0 for unlimited (default: 1000)
            config_manager: ConfigManager instance to use for settings (optional)
        """
        super().__init__()
        self.config_manager = config_manager

        # Use config values if config_manager provided, otherwise use parameters
        if self.config_manager:
            self.max_workers = self.config_manager.get(
                "performance_settings.search_thread_count", max_workers
            )
            self.max_results = self.config_manager.get(
                "search_preferences.max_search_results", max_results
            )
            self.case_sensitive = self.config_manager.get(
                "search_preferences.case_sensitive_search", False
            )
            self.include_hidden = self.config_manager.get(
                "search_preferences.include_hidden_files", False
            )
            self.file_extensions_to_exclude = self.config_manager.get(
                "search_preferences.file_extensions_to_exclude", []
            )
        else:
            self.max_workers = max_workers
            self.max_results = max_results
            self.case_sensitive = False
            self.include_hidden = False
            self.file_extensions_to_exclude = []

        self._cancelled = False
        self._executor: Optional[ThreadPoolExecutor] = None
        self.plugin_manager = plugin_manager
        self.progress_callback = progress_callback

        # Progress throttling
        self._last_progress_time = 0
        self._progress_throttle_ms = 100  # 10 updates per second max

        # Status update throttling
        self._last_status_time = 0
        self._status_throttle_ms = 200  # 5 updates per second max

        logger.debug(
            f"FileSearchEngine initialized with max_workers={self.max_workers}, "
            f"max_results={self.max_results}, case_sensitive={self.case_sensitive}"
        )

    def set_progress_callback(self, callback) -> None:
        """Set the progress callback function.

        Args:
            callback: Function to call for progress updates
            (files_scanned: int, current_dir: str)
        """
        self.progress_callback = callback

    def cancel(self) -> None:
        """Cancel current search operation."""
        self._cancelled = True
        logger.info("Search cancellation requested")

    def _should_cancel(self) -> bool:
        """Check if search should be cancelled.

        Returns:
            True if search should be cancelled, False otherwise
        """
        return self._cancelled

    def _reset_cancel_state(self) -> None:
        """Reset cancellation state for new search."""
        self._cancelled = False

    def _match_pattern(self, filename: str, pattern: str) -> bool:
        """Check if filename matches search pattern.

        Args:
            filename: Name of file to check
            pattern: Search pattern (supports wildcards with fnmatch)

        Returns:
            True if filename matches pattern, False otherwise
        """
        try:
            if self.case_sensitive:
                return fnmatch.fnmatch(filename, pattern)
            else:
                return fnmatch.fnmatch(filename.lower(), pattern.lower())
        except Exception as e:
            logger.error(
                f"Error matching pattern '{pattern}' against '{filename}': {e}"
            )
            return False

    def _scan_directory(
        self, directory: Path, pattern: str, results: Set[Path], depth: int = 0
    ) -> None:
        """Scan a single directory for matching files.

        Args:
            directory: Directory path to scan
            pattern: Search pattern to match
            results: Set to store matching file paths
            depth: Current recursion depth (for symlink cycle detection)

        Note:
            This method is designed to be called from worker threads.
            Uses os.scandir() for efficient directory traversal.
        """
        if self._should_cancel():
            logger.debug(f"Cancelling scan of {directory}")
            return

        # Check for symlink cycle detection (max depth 10)
        if depth > 10:
            logger.warning(f"Maximum symlink depth (10) reached at {directory}")
            return

        try:
            logger.debug(f"Scanning directory: {directory}")

            with os.scandir(directory) as entries:
                for entry in entries:
                    if self._should_cancel():
                        break

                    try:
                        # Skip hidden files/directories if not including them
                        if not self.include_hidden and entry.name.startswith("."):
                            continue

                        if entry.is_file():
                            # Check file extension exclusions
                            if self.file_extensions_to_exclude:
                                file_ext = Path(entry.name).suffix.lower()
                                if file_ext in [
                                    ext.lower()
                                    for ext in self.file_extensions_to_exclude
                                ]:
                                    continue

                            if self._match_pattern(entry.name, pattern):
                                results.add(Path(entry.path))
                                logger.debug(f"Match found: {entry.path}")

                                # Emit status update (throttled)
                                current_time = time.time() * 1000  # milliseconds
                                if (
                                    current_time - self._last_status_time
                                    >= self._status_throttle_ms
                                ):
                                    self.results_count_update.emit(1, len(results))
                                    self._last_status_time = current_time

                                # Call progress callback if provided (throttled)
                                if self.progress_callback:
                                    current_time = time.time() * 1000  # milliseconds
                                    if (
                                        current_time - self._last_progress_time
                                        >= self._progress_throttle_ms
                                    ):
                                        try:
                                            self.progress_callback(
                                                len(results), str(directory)
                                            )
                                            self._last_progress_time = current_time
                                        except Exception as e:
                                            logger.warning(
                                                f"Progress callback error: {e}"
                                            )

                                # Check if we've reached max results
                                if (
                                    self.max_results > 0
                                    and len(results) >= self.max_results
                                ):
                                    self._cancelled = True
                                    break

                        elif entry.is_dir():
                            # Skip hidden directories if not including them
                            if not self.include_hidden and entry.name.startswith("."):
                                continue

                            # Handle symlinks with cycle detection
                            if entry.is_symlink():
                                try:
                                    # Resolve symlink and check if it creates a cycle
                                    resolved_path = Path(entry.path).resolve()
                                    # Simple cycle detection by checking if
                                    # resolved path is within current path
                                    if directory in resolved_path.parents:
                                        logger.warning(
                                            f"Symlink cycle detected: {entry.path} -> "
                                            f"{resolved_path}"
                                        )
                                        continue
                                    # Recursively scan resolved symlink directory
                                    self._scan_directory(
                                        resolved_path, pattern, results, depth + 1
                                    )
                                except (OSError, PermissionError) as e:
                                    logger.warning(
                                        f"Cannot resolve symlink {entry.path}: {e}"
                                    )
                                    continue
                            else:
                                # Regular directory - recurse normally
                                self._scan_directory(
                                    Path(entry.path), pattern, results, depth + 1
                                )

                    except (PermissionError, OSError) as e:
                        logger.warning(
                            f"Access denied or error accessing {entry.path}: {e}"
                        )
                        continue

        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot access directory {directory}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scanning {directory}: {e}")
            raise SearchError(f"Error scanning directory {directory}: {e}")

    def estimate_total_files(self, directory: Path) -> int:
        """Estimate total number of files in directory for progress calculation.

        Args:
            directory: Directory to scan

        Returns:
            Estimated total file count
        """
        try:
            total = 0
            for root, dirs, files in os.walk(directory):
                # Skip hidden directories
                dirs[:] = [
                    d for d in dirs if not d.startswith(".") or self.include_hidden
                ]
                total += len(files)
                # Limit depth for performance
                if root.count(os.sep) - directory.as_posix().count(os.sep) > 3:
                    break
            return total
        except Exception as e:
            logger.warning(f"Error estimating total files: {e}")
            return 0

    def search(
        self, directory: Path, query: str
    ) -> Generator[Dict[str, Any], None, None]:
        """Search for files matching query pattern.

        Args:
            directory: Root directory to start search from
            query: Search pattern (supports wildcards with fnmatch syntax)

        Yields:
            Dict objects for matching files/results with keys:
            'path', 'name', 'source', etc.

        Raises:
            SearchError: If directory doesn't exist or is not accessible
            ValueError: If directory is not a valid path

        Example:
            >>> engine = FileSearchEngine(max_results=100)
            >>> for result in engine.search(Path('/home/user'), '*.py'):
            ...     print(result['path'])
        """
        logger.info(f"Starting search in {directory} for pattern '{query}'")

        # Validate inputs
        if not directory or not query:
            raise ValueError("Directory and query must not be empty")

        if not isinstance(directory, Path):
            directory = Path(directory)

        if not directory.exists():
            raise SearchError(f"Directory does not exist: {directory}")

        if not directory.is_dir():
            raise SearchError(f"Path is not a directory: {directory}")

        # Reset cancellation state
        self._reset_cancel_state()

        # Use a thread-safe set to store results
        results: Set[Path] = set()

        try:
            # Emit searching status
            self.status_update.emit("searching", 0)

            # Use ThreadPoolExecutor for parallel directory scanning
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self._executor = executor

                # Submit root directory for scanning
                future = executor.submit(
                    self._scan_directory, directory, query, results, 0
                )

                # Wait for scan to complete
                try:
                    future.result()  # Wait for scanning to complete
                except Exception as e:
                    logger.error(f"Error in search execution: {e}")
                    raise SearchError(f"Search execution failed: {e}")

                # Emit completed status
                self.status_update.emit("completed", len(results))

                # Yield all results found (even if cancelled due to max results)
                for path in results:
                    try:
                        stat = path.stat()
                        yield {
                            "path": str(path),
                            "name": path.name,
                            "source": "filesystem",
                            "size": stat.st_size,
                            "modified": stat.st_mtime,
                        }
                    except Exception as e:
                        logger.error(f"Error getting stat for {path}: {e}")
                results.clear()

                # Get plugin results
                if self.plugin_manager:
                    context = {
                        "directory": str(directory),
                        "query": query,
                        "max_results": self.max_results,
                    }
                    for plugin in self.plugin_manager.get_loaded_plugins():
                        if plugin.enabled:
                            try:
                                plugin_results = plugin.search(query, context)
                                for result in plugin_results:
                                    yield result
                            except Exception as e:
                                logger.error(f"Plugin {plugin.name} search failed: {e}")

            logger.info(f"Search completed. Cancelled: {self._should_cancel()}")

        except Exception as e:
            logger.error(f"Search failed: {e}")
            self.status_update.emit("error", 0)
            raise SearchError(f"Search operation failed: {e}")
        finally:
            self._executor = None


# Convenience function for simple searches
def search_files(
    directory: Path, pattern: str, max_results: int = 1000, max_workers: int = 4
) -> Generator[Dict[str, Any], None, None]:
    """Convenience function for one-off file searches.

    Args:
        directory: Directory to search in
        pattern: File pattern to match
        max_results: Maximum number of results (default: 1000)
        max_workers: Number of worker threads (default: 4)

    Yields:
        Dict objects for matching files with keys: 'path', 'name', 'source', etc.

    Example:
        >>> for result in search_files(Path('.'), '*.txt', max_results=50):
        ...     print(result['path'])
    """
    engine = FileSearchEngine(max_workers=max_workers, max_results=max_results)
    yield from engine.search(directory, pattern)
