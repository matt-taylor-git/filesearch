"""Sorting engine for search results.

Provides multiple sorting strategies for search results including
name, size, date, type, and relevance sorting.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Callable, List

from natsort import natsorted

from ..models.search_result import SearchResult


class SortCriteria(Enum):
    """Enum defining available sort criteria."""

    NAME_ASC = "name_asc"
    NAME_DESC = "name_desc"
    SIZE_ASC = "size_asc"
    SIZE_DESC = "size_desc"
    DATE_DESC = "date_desc"  # Newest first
    DATE_ASC = "date_asc"  # Oldest first
    TYPE_ASC = "type_asc"
    RELEVANCE_DESC = "relevance_desc"


@dataclass
class SortResult:
    """Result of a sorting operation."""

    sorted_results: List[SearchResult]
    execution_time_ms: float
    item_count: int


class SortEngine:
    """Engine for sorting search results using various criteria.

    Provides efficient sorting algorithms optimized for large datasets.
    All sorting methods maintain stable sort where applicable.
    """

    @staticmethod
    def sort_by_name(results: List[SearchResult], reverse: bool = False) -> List[SearchResult]:
        """Sort results alphabetically by filename using natural sorting.

        Folders are grouped separately and sorted before files.
        Uses natural sorting to handle numbers correctly (file1, file2, file10).

        Args:
            results: List of SearchResult objects to sort
            reverse: If True, sort in descending order (Z-A)

        Returns:
            Sorted list of SearchResult objects

        AC1 Implementation: Natural sorting with folder grouping
        """
        # Separate folders and files
        folders = [r for r in results if r.path.is_dir()]
        files = [r for r in results if not r.path.is_dir()]

        # Sort folders
        folder_names = [f.path.name for f in folders]
        sorted_folder_indices = natsorted(range(len(folder_names)), key=lambda i: folder_names[i].lower(), reverse=reverse)
        sorted_folders = [folders[i] for i in sorted_folder_indices]

        # Sort files
        file_names = [f.path.name for f in files]
        sorted_file_indices = natsorted(range(len(file_names)), key=lambda i: file_names[i].lower(), reverse=reverse)
        sorted_files = [files[i] for i in sorted_file_indices]

        # Combine: folders first, then files
        return sorted_folders + sorted_files

    @staticmethod
    def sort_by_size(results: List[SearchResult], reverse: bool = False) -> List[SearchResult]:
        """Sort results by file size.

        Folders are treated as size 0 and placed based on sort direction.
        For ascending sort, folders appear first. For descending, folders appear last.

        Args:
            results: List of SearchResult objects to sort
            reverse: If True, sort largest to smallest

        Returns:
            Sorted list of SearchResult objects

        AC2 Implementation: Size sorting with folder handling
        """
        def _get_sort_key(result: SearchResult) -> tuple:
            """Create sort key that handles folders appropriately."""
            is_directory = result.path.is_dir()

            if reverse:
                # For descending (largest first):
                # - Folders should go last, so return (1, size)
                # - Files should sort by size (negative for descending)
                return (1, 0) if is_directory else (0, -result.size)
            else:
                # For ascending (smallest first):
                # - Folders should go first, so return (0, 0)
                # - Files should sort by size
                return (0, 0) if is_directory else (1, result.size)

        return sorted(results, key=_get_sort_key)

    @staticmethod
    def sort_by_date(results: List[SearchResult], reverse: bool = False) -> List[SearchResult]:
        """Sort results by modification date.

        Args:
            results: List of SearchResult objects to sort
            reverse: If True, sort oldest to newest (ascending by timestamp)

        Returns:
            Sorted list of SearchResult objects

        AC3 Implementation: Date sorting with timestamp comparison
        """
        return sorted(results, key=lambda r: r.modified, reverse=not reverse)

    @staticmethod
    def sort_by_type(results: List[SearchResult], reverse: bool = False) -> List[SearchResult]:
        """Sort results by file type.

        Groups items by type: folders first, then files sorted by extension.
        Within each group, items are sorted alphabetically.

        Args:
            results: List of SearchResult objects to sort
            reverse: If True, reverse the overall order

        Returns:
            Sorted list of SearchResult objects

        AC4 Implementation: Type grouping with alphabetical sorting
        """
        def _get_type_sort_key(result: SearchResult) -> tuple:
            """Create sort key for type-based sorting."""
            if result.path.is_dir():
                # Folders first, then sort by name
                return (0, result.path.name.lower())
            else:
                # Files second, group by extension then name
                ext = result.path.suffix.lower()
                return (1, ext, result.path.name.lower())

        sorted_results = sorted(results, key=_get_type_sort_key)

        if reverse:
            sorted_results.reverse()

        return sorted_results

    @staticmethod
    def sort_by_relevance(results: List[SearchResult], query: str) -> List[SearchResult]:
        """Sort results by relevance to search query.

        Calculates match score based on query position in filename:
        - Exact match: highest score (100)
        - Starts with query: high score (80 + length_ratio)
        - Contains query: medium score (40 + position_penalty)
        - Ends with query: lower score (20 + length_ratio)

        Args:
            results: List of SearchResult objects to sort
            query: Search query string

        Returns:
            Sorted list of SearchResult objects (most relevant first)

        AC5 Implementation: Relevance scoring based on match quality
        """
        query_lower = query.lower()

        def _calculate_relevance(result: SearchResult) -> float:
            """Calculate relevance score for a single result."""
            filename_lower = result.path.name.lower()

            if filename_lower == query_lower:
                # Exact match - highest priority
                return 100.0

            if filename_lower.startswith(query_lower):
                # Starts with query - high priority
                # Bonus for closer match length
                length_ratio = len(query) / len(result.path.name)
                return 80.0 + (length_ratio * 20.0)

            if query_lower in filename_lower:
                # Contains query - medium priority
                # Penalty based on position (earlier is better)
                position = filename_lower.index(query_lower)
                position_penalty = position / len(filename_lower) * 20.0
                return 60.0 - position_penalty

            if filename_lower.endswith(query_lower):
                # Ends with query - lower priority
                length_ratio = len(query) / len(result.path.name)
                return 40.0 + (length_ratio * 10.0)

            # No match - lowest priority
            return 0.0

        # Sort by relevance score descending
        return sorted(results, key=_calculate_relevance, reverse=True)

    @classmethod
    def sort(cls, results: List[SearchResult], criteria: SortCriteria, query: str = "") -> List[SearchResult]:
        """Sort results using the specified criteria.

        Args:
            results: List of SearchResult objects to sort
            criteria: SortCriteria enum value
            query: Search query (required for RELEVANCE_DESC sorting)

        Returns:
            Sorted list of SearchResult objects

        Raises:
            ValueError: If query is required but not provided for relevance sorting
        """
        if criteria == SortCriteria.NAME_ASC:
            return cls.sort_by_name(results, reverse=False)

        elif criteria == SortCriteria.NAME_DESC:
            return cls.sort_by_name(results, reverse=True)

        elif criteria == SortCriteria.SIZE_ASC:
            return cls.sort_by_size(results, reverse=False)

        elif criteria == SortCriteria.SIZE_DESC:
            return cls.sort_by_size(results, reverse=True)

        elif criteria == SortCriteria.DATE_ASC:
            return cls.sort_by_date(results, reverse=True)

        elif criteria == SortCriteria.DATE_DESC:
            return cls.sort_by_date(results, reverse=False)

        elif criteria == SortCriteria.TYPE_ASC:
            return cls.sort_by_type(results, reverse=False)

        elif criteria == SortCriteria.RELEVANCE_DESC:
            if not query:
                raise ValueError("Query parameter is required for relevance sorting")
            return cls.sort_by_relevance(results, query)

        else:
            raise ValueError(f"Unknown sort criteria: {criteria}")
