"""
HighlightEngine - Utility class for search result text highlighting

Provides efficient text highlighting for search results with case-insensitive
matching, wildcard support, and regex metacharacter escaping.
"""

import re
from typing import Dict, List, Optional, Tuple


class HighlightEngine:
    """Engine for highlighting matching text in search results"""

    def __init__(self, max_cache_size: int = 10000):
        """
        Initialize the highlight engine

        Args:
            max_cache_size: Max entries in highlight cache (default: 10000)
        """
        self._pattern_cache: Dict[str, re.Pattern] = {}
        self._highlight_cache: Dict[Tuple[str, str], List[Tuple[int, int]]] = {}
        self.max_cache_size = max_cache_size

    def _escape_regex(self, text: str) -> str:
        """
        Escape regex metacharacters in search query

        Args:
            text: The text to escape

        Returns:
            Escaped text safe for regex use
        """
        return re.escape(text)

    def _convert_wildcards(self, query: str) -> str:
        """
        Convert wildcard patterns to regex patterns

        Args:
            query: Query string with wildcards (* and ?)

        Returns:
            Regex pattern string
        """
        # Replace * with .*, ? with .
        pattern = query.replace("*", ".*").replace("?", ".")
        return pattern

    def _should_highlight(self, query: str) -> bool:
        """
        Determine if highlighting should be applied for this query

        Args:
            query: The search query

        Returns:
            True if highlighting should be applied, False otherwise
        """
        if not query:
            return False

        # Check if query contains only wildcards (*, ?, .)
        # . is a wildcard in regex (matches any single character)
        wildcard_only = all(c in "*?." for c in query)
        if wildcard_only:
            return False

        return True

    def _compile_pattern(
        self, query: str, case_sensitive: bool = False
    ) -> Optional[re.Pattern]:
        """
        Compile a regex pattern for the query

        Args:
            query: The search query
            case_sensitive: Whether matching should be case sensitive

        Returns:
            Compiled regex pattern or None if compilation fails
        """
        if not self._should_highlight(query):
            return None

        cache_key = f"{query}_{'cs' if case_sensitive else 'ci'}"

        if cache_key in self._pattern_cache:
            return self._pattern_cache[cache_key]

        try:
            # Convert wildcards to regex
            pattern_str = self._convert_wildcards(query)

            # Add case-insensitive flag
            flags = 0 if case_sensitive else re.IGNORECASE

            # Compile pattern
            pattern = re.compile(pattern_str, flags)

            # Cache the compiled pattern
            self._pattern_cache[cache_key] = pattern

            return pattern
        except (re.error, TypeError):
            # If pattern compilation fails, return None
            return None

    def find_matches(
        self, filename: str, query: str, case_sensitive: bool = False
    ) -> List[Tuple[int, int]]:
        """
        Find all matching substring positions in a filename

        Args:
            filename: The filename to search in
            query: The search query
            case_sensitive: Whether matching should be case sensitive

        Returns:
            List of tuples containing (start_position, end_position) for each match
        """
        if not filename or not query:
            return []

        if not self._should_highlight(query):
            return []

        # Check cache
        cache_key = (filename, query, "cs" if case_sensitive else "ci")
        if cache_key in self._highlight_cache:
            return self._highlight_cache[cache_key]

        pattern = self._compile_pattern(query, case_sensitive)
        if pattern is None:
            return []

        matches = []

        # Remove extension for highlighting purposes
        name_without_ext, ext = self._split_filename_and_ext(filename)

        # Find all matches in the filename (without extension)
        for match in pattern.finditer(name_without_ext):
            matches.append((match.start(), match.end()))

        # Cache the results
        self._highlight_cache[cache_key] = matches

        # Check cache size and prune if needed
        if len(self._highlight_cache) > self.max_cache_size:
            self._prune_cache()

        return matches

    def _split_filename_and_ext(self, filename: str) -> Tuple[str, str]:
        """
        Split filename into name and extension parts

        Args:
            filename: The full filename

        Returns:
            Tuple of (name_without_ext, extension_with_dot)
        """
        # Handle edge cases with multiple dots (e.g., "archive.tar.gz")
        # For now, split at the last dot
        parts = filename.rsplit(".", 1)
        if len(parts) == 2 and len(parts[0]) > 0:
            return parts[0], f".{parts[1]}"
        return filename, ""

    def clear_cache(self):
        """Clear the highlight and pattern caches"""
        self._highlight_cache.clear()
        self._pattern_cache.clear()

    def get_cache_size(self) -> int:
        """Get the current size of the highlight cache

        Returns:
            Number of entries in the highlight cache
        """
        return len(self._highlight_cache)

    def _prune_cache(self):
        """Prune the cache to reduce memory usage when it exceeds max size

        Removes the oldest 20% of entries to make room for new ones
        """
        # Remove oldest 20% of entries
        # Python 3.7+ popitem preserves insertion order (LIFO)
        num_to_remove = len(self._highlight_cache) // 5  # 20%
        for _ in range(num_to_remove):
            try:
                self._highlight_cache.popitem()
            except KeyError:
                break

    def generate_highlighted_html(
        self,
        filename: str,
        query: str,
        case_sensitive: bool = False,
        highlight_color: str = "#FFFF99",
    ) -> str:
        """
        Generate HTML with highlighted matching text

        Args:
            filename: The filename to highlight
            query: The search query
            case_sensitive: Whether matching should be case sensitive
            highlight_color: HTML color code for highlight background

        Returns:
            HTML string with highlighted matches
        """
        matches = self.find_matches(filename, query, case_sensitive)

        if not matches:
            return filename

        # Split filename into name and extension
        name_without_ext, ext = self._split_filename_and_ext(filename)

        # Build highlighted string
        result_parts = []
        last_end = 0

        for start, end in matches:
            # Add non-matching text before this match
            if start > last_end:
                result_parts.append(name_without_ext[last_end:start])

            # Add highlighted matching text
            match_text = name_without_ext[start:end]
            style_attrs = f"background-color: {highlight_color}; font-weight: bold;"
            highlighted = f'<span style="{style_attrs}">{match_text}</span>'
            result_parts.append(highlighted)

            last_end = end

        # Add remaining non-matching text
        if last_end < len(name_without_ext):
            result_parts.append(name_without_ext[last_end:])

        # Add extension (never highlighted)
        result_parts.append(ext)

        return "".join(result_parts)

    def has_matches(
        self, filename: str, query: str, case_sensitive: bool = False
    ) -> bool:
        """
        Check if a filename contains matches for the query

        Args:
            filename: The filename to check
            query: The search query
            case_sensitive: Whether matching should be case sensitive

        Returns:
            True if matches found, False otherwise
        """
        return len(self.find_matches(filename, query, case_sensitive)) > 0


def is_valid_highlight_query(query: str) -> bool:
    """
    Check if a query is valid for highlighting

    Args:
        query: The search query

    Returns:
        True if highlighting should be applied, False otherwise
    """
    if not query:
        return False

    # Check if query contains only wildcards
    wildcard_only = all(c in "*?" for c in query)
    if wildcard_only:
        return False

    return True
