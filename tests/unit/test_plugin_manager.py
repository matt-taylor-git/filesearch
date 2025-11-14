"""Unit tests for PluginManager class."""

from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from filesearch.plugins.plugin_base import SearchPlugin
from filesearch.plugins.plugin_manager import PluginManager


class MockPlugin(SearchPlugin):
    """Mock plugin for testing."""

    def __init__(self, metadata=None):
        super().__init__(metadata)
        self._name = "MockPlugin"

    def initialize(self, config):
        self._config = config
        return True

    def get_name(self):
        return self._name

    def search(self, query, context):
        return []


class TestPluginManager:
    """Test cases for PluginManager."""

    def test_initialization(self):
        """Test PluginManager initialization."""
        manager = PluginManager()
        assert manager._plugins == {}
        assert manager._config_manager is None

    def test_initialization_with_config_manager(self):
        """Test PluginManager initialization with config manager."""
        mock_config = Mock()
        manager = PluginManager(mock_config)
        assert manager._config_manager == mock_config

    def test_get_plugin_not_found(self):
        """Test getting a plugin that doesn't exist."""
        manager = PluginManager()
        assert manager.get_plugin("nonexistent") is None

    def test_enable_disable_plugin(self):
        """Test enabling and disabling plugins."""
        manager = PluginManager()
        mock_plugin = Mock()
        mock_plugin.enabled = False
        manager._plugins["test"] = mock_plugin

        # Enable
        assert manager.enable_plugin("test") is True
        mock_plugin.enabled = True

        # Try to enable again
        assert manager.enable_plugin("test") is False

        # Disable
        assert manager.disable_plugin("test") is True
        mock_plugin.enabled = False

        # Try to disable again
        assert manager.disable_plugin("test") is False

    def test_unload_plugin(self):
        """Test unloading a plugin."""
        manager = PluginManager()
        mock_plugin = Mock()
        manager._plugins["test"] = mock_plugin

        assert manager.unload_plugin("test") is True
        assert "test" not in manager._plugins
        mock_plugin.cleanup.assert_called_once()

    def test_unload_plugin_not_found(self):
        """Test unloading a plugin that doesn't exist."""
        manager = PluginManager()
        assert manager.unload_plugin("nonexistent") is False

    def test_get_plugin_config_no_config_manager(self):
        """Test getting plugin config without config manager."""
        manager = PluginManager()
        assert manager.get_plugin_config("test") == {}

    def test_get_plugin_config_with_config_manager(self):
        """Test getting plugin config with config manager."""
        mock_config = Mock()
        mock_config.get.return_value = {"key": "value"}
        manager = PluginManager(mock_config)

        result = manager.get_plugin_config("test")
        assert result == {"key": "value"}
        mock_config.get.assert_called_once_with("plugins.test", {})

    def test_set_plugin_config_no_config_manager(self):
        """Test setting plugin config without config manager."""
        manager = PluginManager()
        assert manager.set_plugin_config("test", {"key": "value"}) is True

    def test_set_plugin_config_with_config_manager(self):
        """Test setting plugin config with config manager."""
        mock_config = Mock()
        manager = PluginManager(mock_config)

        assert manager.set_plugin_config("test", {"key": "value"}) is True
        mock_config.set.assert_called_once_with("plugins.test", {"key": "value"})
        mock_config.save.assert_called_once()

    def test_get_loaded_plugins(self):
        """Test getting list of loaded plugins."""
        manager = PluginManager()
        mock_plugin = Mock()
        manager._plugins["test"] = mock_plugin

        plugins = manager.get_loaded_plugins()
        assert plugins == [mock_plugin]

    @patch("filesearch.plugins.plugin_manager.PluginManager._discover_from_directory")
    def test_discover_plugins(self, mock_discover):
        """Test plugin discovery."""
        mock_discover.return_value = [(MockPlugin, {})]
        manager = PluginManager()

        plugins = manager.discover_plugins()
        assert len(plugins) == 1
        assert plugins[0][0] == MockPlugin

    def test_load_plugin_invalid_class(self):
        """Test loading an invalid plugin class."""
        manager = PluginManager()

        # Mock invalid plugin class
        class InvalidPlugin:
            pass

        result = manager._load_plugin(InvalidPlugin, {})
        assert result is None

    def test_load_plugin_valid_class(self):
        """Test loading a valid plugin class."""
        manager = PluginManager()

        result = manager._load_plugin(MockPlugin, {})
        assert result is not None
        assert isinstance(result, MockPlugin)

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_from_directory_no_directory(self, mock_glob, mock_exists):
        """Test discovering plugins when directory doesn't exist."""
        mock_exists.return_value = False
        manager = PluginManager()

        result = manager._discover_from_directory(Path("/fake/path"))
        assert result == []
        mock_exists.assert_called_once()

    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.glob")
    def test_discover_from_directory_with_plugins(self, mock_glob, mock_exists):
        """Test discovering plugins from directory."""
        mock_exists.return_value = True
        mock_file = Mock()
        mock_file.name = "test_plugin.py"
        mock_glob.return_value = [mock_file]

        # Mock the import process
        with patch("importlib.util.spec_from_file_location") as mock_spec, patch(
            "importlib.util.module_from_spec"
        ) as mock_module, patch("inspect.getmembers") as mock_members:
            mock_spec.return_value = Mock()
            mock_spec.return_value.loader = Mock()
            mock_module_obj = Mock()
            mock_module.return_value = mock_module_obj
            mock_members.return_value = [("MockPlugin", MockPlugin)]

            manager = PluginManager()
            result = manager._discover_from_directory(Path("/fake/path"))

            assert len(result) == 1
            assert result[0][0] == MockPlugin
