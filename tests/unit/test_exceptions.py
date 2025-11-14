"""Unit tests for the exceptions module.

This module tests the custom exception hierarchy for the File Search application.
"""

import pytest

from filesearch.core.exceptions import (
    ConfigError,
    FileSearchError,
    PluginError,
    SearchError,
    UIError,
)


class TestFileSearchError:
    """Test the base FileSearchError class."""

    def test_basic_error(self):
        """Test basic error creation."""
        error = FileSearchError("Test error message")
        assert str(error) == "Test error message"
        assert error.message == "Test error message"
        assert error.details is None
        assert error.cause is None

    def test_error_with_details(self):
        """Test error with details."""
        error = FileSearchError("Test error", details={"key": "value"})
        assert "Test error" in str(error)
        assert "details: {'key': 'value'}" in str(error)
        assert error.details == {"key": "value"}

    def test_error_with_cause(self):
        """Test error with cause."""
        cause = ValueError("Original error")
        error = FileSearchError("Test error", cause=cause)
        assert error.cause == cause
        assert isinstance(error.cause, ValueError)


class TestSearchError:
    """Test the SearchError class."""

    def test_search_error_basic(self):
        """Test basic search error."""
        error = SearchError("Search failed")
        assert str(error) == "Search failed"
        assert error.path is None
        assert error.pattern is None

    def test_search_error_with_path(self):
        """Test search error with path."""
        error = SearchError("Permission denied", path="/restricted/path")
        assert error.path == "/restricted/path"
        assert "Permission denied" in str(error)

    def test_search_error_with_pattern(self):
        """Test search error with pattern."""
        error = SearchError("Invalid pattern", pattern="**/*.py")
        assert error.pattern == "**/*.py"
        assert "Invalid pattern" in str(error)

    def test_search_error_inheritance(self):
        """Test that SearchError inherits from FileSearchError."""
        error = SearchError("Test")
        assert isinstance(error, FileSearchError)
        assert isinstance(error, Exception)


class TestPluginError:
    """Test the PluginError class."""

    def test_plugin_error_basic(self):
        """Test basic plugin error."""
        error = PluginError("Plugin failed")
        assert str(error) == "Plugin failed"
        assert error.plugin_name is None

    def test_plugin_error_with_name(self):
        """Test plugin error with plugin name."""
        error = PluginError("Loading failed", plugin_name="test_plugin")
        assert error.plugin_name == "test_plugin"
        assert "Loading failed" in str(error)

    def test_plugin_error_inheritance(self):
        """Test that PluginError inherits from FileSearchError."""
        error = PluginError("Test")
        assert isinstance(error, FileSearchError)


class TestConfigError:
    """Test the ConfigError class."""

    def test_config_error_basic(self):
        """Test basic config error."""
        error = ConfigError("Invalid configuration")
        assert str(error) == "Invalid configuration"
        assert error.config_file is None
        assert error.config_key is None

    def test_config_error_with_file(self):
        """Test config error with file path."""
        error = ConfigError("Parse error", config_file="config/settings.toml")
        assert error.config_file == "config/settings.toml"
        assert "Parse error" in str(error)

    def test_config_error_with_key(self):
        """Test config error with config key."""
        error = ConfigError("Invalid value", config_key="search.max_results")
        assert error.config_key == "search.max_results"
        assert "Invalid value" in str(error)

    def test_config_error_inheritance(self):
        """Test that ConfigError inherits from FileSearchError."""
        error = ConfigError("Test")
        assert isinstance(error, FileSearchError)


class TestUIError:
    """Test the UIError class."""

    def test_ui_error_basic(self):
        """Test basic UI error."""
        error = UIError("UI initialization failed")
        assert str(error) == "UI initialization failed"
        assert error.component is None

    def test_ui_error_with_component(self):
        """Test UI error with component name."""
        error = UIError("Widget creation failed", component="MainWindow")
        assert error.component == "MainWindow"
        assert "Widget creation failed" in str(error)

    def test_ui_error_inheritance(self):
        """Test that UIError inherits from FileSearchError."""
        error = UIError("Test")
        assert isinstance(error, FileSearchError)


class TestExceptionHierarchy:
    """Test the complete exception hierarchy."""

    def test_all_exceptions_inherit_from_base(self):
        """Test that all custom exceptions inherit from FileSearchError."""
        exceptions = [
            SearchError("test"),
            PluginError("test"),
            ConfigError("test"),
            UIError("test"),
        ]
        
        for error in exceptions:
            assert isinstance(error, FileSearchError)
            assert isinstance(error, Exception)

    def test_exception_raising_and_catching(self):
        """Test that exceptions can be raised and caught properly."""
        with pytest.raises(FileSearchError):
            raise SearchError("Test search error")
        
        with pytest.raises(SearchError):
            raise SearchError("Specific search error")
        
        with pytest.raises(FileSearchError):
            raise PluginError("Test plugin error")

    def test_exception_with_cause_chain(self):
        """Test exception chaining."""
        original_error = ValueError("Original error")
        search_error = SearchError("Search failed", cause=original_error)
        
        assert search_error.cause == original_error
        assert isinstance(search_error.cause, ValueError)
