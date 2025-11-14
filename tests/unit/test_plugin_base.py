"""Unit tests for the plugin base module."""

import inspect
from abc import ABC
from pathlib import Path
from typing import Dict, Any, List

import pytest

from filesearch.core.exceptions import PluginError
from filesearch.plugins.plugin_base import SearchPlugin, PluginDiscovery, ExamplePlugin


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
        assert hasattr(SearchPlugin, 'initialize')
        assert hasattr(SearchPlugin, 'search')
        assert hasattr(SearchPlugin, 'get_name')
        
        # Check they are abstract
        assert hasattr(SearchPlugin.initialize, '__isabstractmethod__')
        assert hasattr(SearchPlugin.search, '__isabstractmethod__')
        assert hasattr(SearchPlugin.get_name, '__isabstractmethod__')


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
            self.initialized = False
            self.search_called = False
        
        def initialize(self, config: Dict[str, Any]) -> bool:
            """Initialize the mock plugin."""
            self._config = config
            self.initialized = True
            return True
        
        def search(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
            """Perform search (mock implementation)."""
            self.search_called = True
            return [
                {
                    'path': '/test/file1.txt',
                    'name': 'file1.txt',
                    'type': 'text'
                }
            ]
        
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
    
    def test_plugin_initialize(self, mock_plugin):
        """Test plugin initialization."""
        config = {'test': 'value', 'number': 42}
        
        result = mock_plugin.initialize(config)
        
        assert result is True
        assert mock_plugin.initialized is True
        assert mock_plugin.config == config
    
    def test_plugin_search(self, mock_plugin):
        """Test plugin search method."""
        query = "test query"
        context = {'directory': '/test'}
        
        results = mock_plugin.search(query, context)
        
        assert mock_plugin.search_called is True
        assert isinstance(results, list)
        assert len(results) == 1
        assert results[0]['name'] == 'file1.txt'
    
    def test_plugin_get_name(self, mock_plugin):
        """Test plugin get_name method."""
        assert mock_plugin.get_name() == "MockPlugin"
    
    def test_plugin_get_version(self, mock_plugin):
        """Test plugin get_version method."""
        assert mock_plugin.get_version() == "2.0.0"
    
    def test_plugin_update_config(self, mock_plugin):
        """Test plugin update_config method."""
        initial_config = {'initial': 'value'}
        mock_plugin.initialize(initial_config)
        
        new_config = {'new': 'value', 'number': 123}
        result = mock_plugin.update_config(new_config)
        
        assert result is True
        assert 'new' in mock_plugin.config
        assert mock_plugin.config['new'] == 'value'
    
    def test_plugin_validate_config(self, mock_plugin):
        """Test plugin validate_config method."""
        # Default implementation should return True
        assert mock_plugin.validate_config({}) is True
        assert mock_plugin.validate_config({'any': 'config'}) is True
    
    def test_plugin_get_metadata(self, mock_plugin):
        """Test plugin get_metadata method."""
        metadata = mock_plugin.get_metadata()
        
        assert isinstance(metadata, dict)
        assert metadata['name'] == "MockPlugin"
        assert metadata['version'] == "2.0.0"
        assert metadata['author'] == "Test Author"
        assert metadata['description'] == "Mock plugin for testing"
        assert metadata['enabled'] is True
        assert 'config' in metadata
    
    def test_plugin_cleanup(self, mock_plugin):
        """Test plugin cleanup method."""
        # Should not raise exception
        mock_plugin.cleanup()


class TestPluginDiscovery:
    """Test cases for PluginDiscovery class."""
    
    def test_discover_from_nonexistent_directory(self):
        """Test discovering plugins from non-existent directory."""
        nonexistent_dir = Path("/nonexistent/plugins")
        plugins = PluginDiscovery.discover_from_directory(nonexistent_dir)
        
        assert isinstance(plugins, list)
        assert len(plugins) == 0
    
    def test_discover_from_empty_directory(self, tmp_path):
        """Test discovering plugins from empty directory."""
        plugins = PluginDiscovery.discover_from_directory(tmp_path)
        
        assert isinstance(plugins, list)
        assert len(plugins) == 0
    
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
    
    def test_load_plugin_success(self):
        """Test successfully loading a plugin."""
        config = {'test': 'value'}
        plugin = PluginDiscovery.load_plugin(ExamplePlugin, config)
        
        assert plugin is not None
        assert isinstance(plugin, ExamplePlugin)
        assert plugin.get_name() == "Example Size Filter"
    
    def test_load_plugin_with_none_config(self):
        """Test loading a plugin with None config."""
        plugin = PluginDiscovery.load_plugin(ExamplePlugin, None)
        
        assert plugin is not None
        assert isinstance(plugin, ExamplePlugin)
    
    def test_load_plugin_failure(self):
        """Test loading a plugin that fails initialization."""
        class FailingPlugin(SearchPlugin):
            def initialize(self, config):
                return False
            
            def search(self, query, context):
                return []
            
            def get_name(self):
                return "FailingPlugin"
        
        plugin = PluginDiscovery.load_plugin(FailingPlugin, {})
        assert plugin is None
    
    def test_load_plugin_with_invalid_class(self):
        """Test loading an invalid plugin class."""
        plugin = PluginDiscovery.load_plugin(str, {})
        assert plugin is None


class TestExamplePlugin:
    """Test cases for ExamplePlugin."""
    
    def test_example_plugin_instantiation(self):
        """Test ExamplePlugin instantiation."""
        plugin = ExamplePlugin()
        
        assert isinstance(plugin, SearchPlugin)
        assert plugin.get_name() == "Example Size Filter"
        assert plugin.version == "1.0.0"
    
    def test_example_plugin_initialize(self):
        """Test ExamplePlugin initialization."""
        plugin = ExamplePlugin()
        config = {'min_size': 1024, 'max_size': 1048576}
        
        result = plugin.initialize(config)
        
        assert result is True
        assert plugin.config == config
    
    def test_example_plugin_search(self):
        """Test ExamplePlugin search method."""
        plugin = ExamplePlugin()
        plugin.initialize({'min_size': 1024})
        
        query = "*.txt"
        context = {'directory': '/test', 'min_size': 1024}
        
        # Should return empty list (simplified implementation)
        results = plugin.search(query, context)
        
        assert isinstance(results, list)
    
    def test_example_plugin_get_name(self):
        """Test ExamplePlugin get_name method."""
        plugin = ExamplePlugin()
        assert plugin.get_name() == "Example Size Filter"