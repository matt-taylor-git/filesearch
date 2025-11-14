"""Core search engine module for file searching functionality.

This module provides the FileSearchEngine class that implements multi-threaded
file searching with partial matching, early termination, and generator-based
result streaming.
"""

import fnmatch
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Generator, Optional, Set

from loguru import logger

from filesearch.core.exceptions import SearchError


class FileSearchEngine:
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
    
    def __init__(self, max_workers: int = 4, max_results: int = 1000):
        """Initialize the search engine.
        
        Args:
            max_workers: Maximum number of worker threads (default: 4)
            max_results: Maximum results to return, 0 for unlimited (default: 1000)
        """
        self.max_workers = max_workers
        self.max_results = max_results
        self._cancelled = False
        self._executor: Optional[ThreadPoolExecutor] = None
        
        logger.debug(f"FileSearchEngine initialized with max_workers={max_workers}, "
                    f"max_results={max_results}")
    
    def cancel(self) -> None:
        """Cancel the current search operation."""
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
        """Check if filename matches the search pattern.
        
        Args:
            filename: Name of the file to check
            pattern: Search pattern (supports wildcards with fnmatch)
            
        Returns:
            True if filename matches pattern, False otherwise
        """
        try:
            return fnmatch.fnmatch(filename.lower(), pattern.lower())
        except Exception as e:
            logger.error(f"Error matching pattern '{pattern}' against '{filename}': {e}")
            return False
    
    def _scan_directory(self, directory: Path, pattern: str, 
                       results: Set[Path]) -> None:
        """Scan a single directory for matching files.
        
        Args:
            directory: Directory path to scan
            pattern: Search pattern to match
            results: Set to store matching file paths
            
        Note:
            This method is designed to be called from worker threads.
            Uses os.scandir() for efficient directory traversal.
        """
        if self._should_cancel():
            logger.debug(f"Cancelling scan of {directory}")
            return
        
        try:
            logger.debug(f"Scanning directory: {directory}")
            
            with os.scandir(directory) as entries:
                for entry in entries:
                    if self._should_cancel():
                        break
                    
                    try:
                        if entry.is_file():
                            if self._match_pattern(entry.name, pattern):
                                results.add(Path(entry.path))
                                logger.debug(f"Match found: {entry.path}")
                                
                                # Check if we've reached max results
                                if self.max_results > 0 and len(results) >= self.max_results:
                                    logger.info(f"Max results ({self.max_results}) reached, "
                                              f"stopping search")
                                    self.cancel()  # Signal other threads to stop
                                    break
                        
                        elif entry.is_dir() and not entry.is_symlink():
                            # Recursively scan subdirectories
                            self._scan_directory(Path(entry.path), pattern, results)
                            
                    except (PermissionError, OSError) as e:
                        logger.warning(f"Access denied or error accessing {entry.path}: {e}")
                        continue
                    
        except (PermissionError, OSError) as e:
            logger.warning(f"Cannot access directory {directory}: {e}")
        except Exception as e:
            logger.error(f"Unexpected error scanning {directory}: {e}")
            raise SearchError(f"Error scanning directory {directory}: {e}")
    
    def search(self, directory: Path, query: str) -> Generator[Path, None, None]:
        """Search for files matching the query pattern.
        
        Args:
            directory: Root directory to start search from
            query: Search pattern (supports wildcards with fnmatch syntax)
            
        Yields:
            Path objects for matching files
            
        Raises:
            SearchError: If directory doesn't exist or is not accessible
            ValueError: If directory is not a valid path
            
        Example:
            >>> engine = FileSearchEngine(max_results=100)
            >>> for path in engine.search(Path('/home/user'), '*.py'):
            ...     print(path)
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
            # Use ThreadPoolExecutor for parallel directory scanning
            with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
                self._executor = executor
                
                # Submit root directory for scanning
                future = executor.submit(self._scan_directory, directory, query, results)
                
                # Wait for completion or cancellation
                while not future.done() and not self._should_cancel():
                    # Yield any results found so far for real-time streaming
                    if results:
                        for path in list(results):
                            yield path
                            results.remove(path)
                    
                    # Small delay to avoid busy waiting
                    import time
                    time.sleep(0.01)
                
                # Ensure we get the final results
                try:
                    future.result(timeout=1.0)
                except Exception as e:
                    logger.error(f"Error in search execution: {e}")
                    raise SearchError(f"Search execution failed: {e}")
                
                # Yield any remaining results
                for path in results:
                    yield path
                
                results.clear()
            
            logger.info(f"Search completed. Cancelled: {self._should_cancel()}")
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            raise SearchError(f"Search operation failed: {e}")
        finally:
            self._executor = None


# Convenience function for simple searches
def search_files(directory: Path, pattern: str, max_results: int = 1000,
                max_workers: int = 4) -> Generator[Path, None, None]:
    """Convenience function for one-off file searches.
    
    Args:
        directory: Directory to search in
        pattern: File pattern to match
        max_results: Maximum number of results (default: 1000)
        max_workers: Number of worker threads (default: 4)
        
    Yields:
        Path objects for matching files
        
    Example:
        >>> for path in search_files(Path('.'), '*.txt', max_results=50):
        ...     print(path)
    """
    engine = FileSearchEngine(max_workers=max_workers, max_results=max_results)
    yield from engine.search(directory, pattern)