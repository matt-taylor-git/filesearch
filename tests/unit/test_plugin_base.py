"""Unit tests for the plugin base module."""

import inspect
from abc import ABC
from typing import Any

import pytest

from filesearch.plugins.builtin.example_plugin import ExamplePlugin
from filesearch.plugins.plugin_base import PluginDiscovery, SearchPlugin


class TestSearchPlugin:
    """Test cases for SearchPlugin abstract base class."""

    def test_search_plugin_is_abstract(self):
        """Test that SearchPlugin is an abstract base class."""
        assert inspect.isclass(SearchPlugin)
        assert issubclass(SearchPlugin, ABC)

    def test_cannot_instantiate_search_plugin_directly(self):
        """Test that SearchPlugin cannot be instantiated directly."""
        with pytest.raises(TypeError):
            SearchPlugin()

    def test_has_required_abstract_methods(self):
        """Test that SearchPlugin has required abstract methods."""
        assert hasattr(SearchPlugin, "initialize")
        assert hasattr(SearchPlugin, "search")
        assert hasattr(SearchPlugin, "get_name")

        # Check they are abstract
        assert hasattr(SearchPlugin.initialize, "__isabstractmethod__")
        assert hasattr(SearchPlugin.search, "__isabstractmethod__")
        assert hasattr(SearchPlugin.get_name, "__isabstractmethod__")


class TestConcretePlugin:
    """Test cases using a concrete plugin implementation."""

    class MockPlugin(SearchPlugin):
        """Mock plugin for testing."""

        def __init__(self):
            super().__init__()
            self._name = "MockPlugin"
            self._version = "2.0.0"
            self._author = "Test Author"
            self._description = "Mock plugin for testing"

        def initialize(self, config: dict[str, Any]) -> bool:
            """Initialize the mock plugin."""
            self._config = config
            return True

        def search(self, query: str, context: dict[str, Any]) -> list[dict[str, Any]]:
            """Perform search (mock implementation)."""
            return []

        def get_name(self) -> str:
            """Get plugin name."""
            return self._name

    @pytest.fixture
    def mock_plugin(self):
        """Create a mock plugin instance."""
        return self.MockPlugin()

    def test_concrete_plugin_can_be_instantiated(self, mock_plugin):
        """Test that concrete plugin can be instantiated."""
        assert isinstance(mock_plugin, SearchPlugin)
        assert isinstance(mock_plugin, self.MockPlugin)

    def test_plugin_default_properties(self, mock_plugin):
        """Test plugin default properties."""
        assert mock_plugin.name == "MockPlugin"
        assert mock_plugin.version == "2.0.0"
        assert mock_plugin.author == "Test Author"
        assert mock_plugin.description == "Mock plugin for testing"
        assert mock_plugin.enabled is True

    def test_plugin_enabled_setter(self, mock_plugin):
        """Test plugin enabled property setter."""
        assert mock_plugin.enabled is True

        mock_plugin.enabled = False
        assert mock_plugin.enabled is False

        mock_plugin.enabled = True
        assert mock_plugin.enabled is True

    def test_plugin_get_version(self, mock_plugin):
        """Test plugin get_version method."""
        assert mock_plugin.get_version() == "2.0.0"

    def test_plugin_update_config(self, mock_plugin):
        """Test plugin update_config method."""
        initial_config = {"initial": "value"}
        mock_plugin.initialize(initial_config)

        new_config = {"new": "value", "number": 123}
        result = mock_plugin.update_config(new_config)

        assert result is True
        assert "new" in mock_plugin.config
        assert mock_plugin.config["new"] == "value"

    def test_plugin_validate_config(self, mock_plugin):
        """Test plugin validate_config method."""
        # Default implementation should return True
        assert mock_plugin.validate_config({}) is True
        assert mock_plugin.validate_config({"any": "config"}) is True

    def test_plugin_get_metadata(self, mock_plugin):
        """Test plugin get_metadata method."""
        metadata = mock_plugin.get_metadata()

        assert isinstance(metadata, dict)
        assert metadata["name"] == "MockPlugin"
        assert metadata["version"] == "2.0.0"
        assert metadata["author"] == "Test Author"
        assert metadata["description"] == "Mock plugin for testing"
        assert metadata["enabled"] is True
        assert "config" in metadata

    def test_plugin_cleanup(self, mock_plugin):
        """Test plugin cleanup method."""
        # Should not raise exception
        mock_plugin.cleanup()


class TestPluginDiscovery:
    """Test cases for PluginDiscovery class."""

    def test_is_valid_plugin_with_valid_plugin(self):
        """Test validating a valid plugin class."""
        assert PluginDiscovery.is_valid_plugin(ExamplePlugin) is True

    def test_is_valid_plugin_with_abstract_class(self):
        """Test validating the abstract base class."""
        assert PluginDiscovery.is_valid_plugin(SearchPlugin) is False

    def test_is_valid_plugin_with_non_class(self):
        """Test validating a non-class object."""
        assert PluginDiscovery.is_valid_plugin("not a class") is False
        assert PluginDiscovery.is_valid_plugin(123) is False
        assert PluginDiscovery.is_valid_plugin(None) is False
