"""Example plugin demonstrating plugin structure for File Search.

This plugin provides search functionality for recently accessed files.
It serves as a template for creating custom plugins.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, List

from loguru import logger

from filesearch.plugins.plugin_base import SearchPlugin


class ExamplePlugin(SearchPlugin):
    """Example plugin that searches recently accessed files.

    This plugin maintains a list of recently accessed files and allows
    searching through them. It demonstrates the basic plugin structure
    and serves as a template for custom plugins.
    """

    def __init__(self, metadata=None):
        """Initialize the example plugin."""
        super().__init__(metadata)
        self._recent_files: List[Dict[str, Any]] = []
        self._max_recent_files = 100
        self._name = "Recent Files Search"

    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the plugin with configuration.

        Args:
            config: Configuration dictionary

        Returns:
            True if initialization successful
        """
        try:
            self._config = config
            self._max_recent_files = config.get("max_recent_files", 100)

            # Load recent files from config if available
            recent_files_config = config.get("recent_files", [])
            self._recent_files = recent_files_config

            logger.info(
                f"ExamplePlugin initialized with {len(self._recent_files)} recent files"
            )
            return True

        except Exception as e:
            logger.error(f"ExamplePlugin initialization failed: {e}")
            return False

    def get_name(self) -> str:
        """Get the plugin name.

        Returns:
            Plugin name
        """
        return self._name

    def search(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform search on recent files.

        Args:
            query: Search query string
            context: Search context

        Returns:
            List of search results
        """
        results = []

        try:
            # Simple case-insensitive substring search
            query_lower = query.lower()

            for file_info in self._recent_files:
                file_path = file_info.get("path", "")
                file_name = Path(file_path).name

                # Check if query matches filename
                if query_lower in file_name.lower():
                    # Create result in expected format
                    result = {
                        "path": file_path,
                        "name": file_name,
                        "size": file_info.get("size", 0),
                        "modified": file_info.get("modified", 0),
                        "source": self._name,
                    }
                    results.append(result)

            logger.debug(
                f"ExamplePlugin found {len(results)} matches for query '{query}'"
            )
            return results

        except Exception as e:
            logger.error(f"ExamplePlugin search failed: {e}")
            return []

    def add_recent_file(self, file_path: str) -> None:
        """Add a file to the recent files list.

        Args:
            file_path: Path to the file
        """
        try:
            path = Path(file_path)
            if not path.exists():
                return

            # Get file info
            stat = path.stat()
            file_info = {
                "path": str(path),
                "size": stat.st_size,
                "modified": stat.st_mtime,
            }

            # Remove if already exists
            self._recent_files = [
                f for f in self._recent_files if f["path"] != str(path)
            ]

            # Add to beginning
            self._recent_files.insert(0, file_info)

            # Trim to max size
            self._recent_files = self._recent_files[: self._max_recent_files]

            # Update config
            self._config["recent_files"] = self._recent_files

            logger.debug(f"Added recent file: {file_path}")

        except Exception as e:
            logger.error(f"Error adding recent file {file_path}: {e}")

    def get_recent_files(self) -> List[Dict[str, Any]]:
        """Get the list of recent files.

        Returns:
            List of recent file info dictionaries
        """
        return self._recent_files.copy()

    def clear_recent_files(self) -> None:
        """Clear the recent files list."""
        self._recent_files = []
        self._config["recent_files"] = []
        logger.info("Cleared recent files list")
