"""Unit tests for ExamplePlugin class."""

from pathlib import Path
from unittest.mock import patch

import pytest

from filesearch.plugins.builtin.example_plugin import ExamplePlugin


class TestExamplePlugin:
    """Test cases for ExamplePlugin."""

    def test_initialization(self):
        """Test plugin initialization."""
        plugin = ExamplePlugin()
        assert plugin.get_name() == "Recent Files Search"
        assert plugin._recent_files == []
        assert plugin._max_recent_files == 100

    def test_initialize_success(self):
        """Test successful initialization."""
        plugin = ExamplePlugin()
        config = {"max_recent_files": 50, "recent_files": [{"path": "/test/file.txt"}]}

        result = plugin.initialize(config)
        assert result is True
        assert plugin._max_recent_files == 50
        assert len(plugin._recent_files) == 1

    def test_initialize_failure(self):
        """Test initialization failure."""
        plugin = ExamplePlugin()

        # Create a config dict that will cause an exception when accessed
        class BadConfig(dict):
            def get(self, key, default=None):
                raise Exception("Test error")

        result = plugin.initialize(BadConfig())
        assert result is False

    def test_search_no_matches(self):
        """Test search with no matches."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        results = plugin.search("nonexistent", {})
        assert results == []

    def test_search_with_matches(self):
        """Test search with matches."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        # Add a recent file
        plugin.add_recent_file(__file__)  # This test file

        # Search for the filename
        filename = Path(__file__).name
        results = plugin.search(filename, {})

        assert len(results) == 1
        assert results[0]["name"] == filename
        assert results[0]["source"] == "Recent Files Search"

    def test_add_recent_file(self):
        """Test adding a recent file."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        test_file = __file__
        plugin.add_recent_file(test_file)

        assert len(plugin._recent_files) == 1
        assert plugin._recent_files[0]["path"] == test_file

    def test_add_recent_file_nonexistent(self):
        """Test adding a nonexistent file."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        plugin.add_recent_file("/nonexistent/file.txt")
        assert len(plugin._recent_files) == 0

    def test_add_recent_file_duplicate(self):
        """Test adding the same file multiple times."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        test_file = __file__
        plugin.add_recent_file(test_file)
        plugin.add_recent_file(test_file)

        # Should only have one entry
        assert len(plugin._recent_files) == 1

    def test_get_recent_files(self):
        """Test getting recent files list."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        plugin.add_recent_file(__file__)
        recent_files = plugin.get_recent_files()

        assert len(recent_files) == 1
        assert recent_files[0]["path"] == __file__

    def test_clear_recent_files(self):
        """Test clearing recent files."""
        plugin = ExamplePlugin()
        plugin.initialize({})

        plugin.add_recent_file(__file__)
        assert len(plugin._recent_files) == 1

        plugin.clear_recent_files()
        assert len(plugin._recent_files) == 0

    def test_max_recent_files_limit(self):
        """Test that max_recent_files limit is enforced."""
        plugin = ExamplePlugin()
        plugin.initialize({"max_recent_files": 2})

        # Add more files than the limit
        for i in range(5):
            temp_file = f"/tmp/test_file_{i}.txt"
            # Create a temporary file for testing
            Path(temp_file).touch()
            try:
                plugin.add_recent_file(temp_file)
            finally:
                Path(temp_file).unlink(missing_ok=True)

        assert len(plugin._recent_files) <= 2
