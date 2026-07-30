"""Integration tests for the plugin system."""

from pathlib import Path
from unittest.mock import Mock

import pytest

from filesearch.core.config_manager import ConfigManager
from filesearch.plugins.plugin_manager import PluginManager


class TestPluginSystemIntegration:
    """Integration tests for the complete plugin system."""

    @pytest.fixture
    def config_manager(self, application_runtime):
        return ConfigManager(runtime=application_runtime, watch_config=False)

    @pytest.fixture
    def manager(self, config_manager):
        return PluginManager(config_manager)

    def test_plugin_manager_load_builtin_plugins(self, manager):
        """Test loading plugins from builtin directory."""

        # The builtin directory should exist and contain example_plugin.py
        builtin_dir = (
            Path(__file__).parent.parent.parent
            / "src"
            / "filesearch"
            / "plugins"
            / "builtin"
        )
        assert builtin_dir.exists()

        plugins = manager.discover_plugins()
        assert len(plugins) >= 1  # At least ExamplePlugin

        # Check that ExamplePlugin is discovered
        plugin_names = [cls.__name__ for cls, meta in plugins]
        assert "ExamplePlugin" in plugin_names

    def test_plugin_manager_load_plugins_integration(self, manager):
        """Test the complete plugin loading process."""

        loaded_plugins = manager.load_plugins()

        # Should load at least the ExamplePlugin
        assert len(loaded_plugins) >= 1

        # Check that plugins are properly initialized
        for plugin in loaded_plugins:
            assert plugin.enabled is True  # Default enabled
            assert plugin.get_name() is not None

    def test_plugin_lifecycle_integration(self, manager):
        """Test complete plugin lifecycle."""

        # Load plugins
        loaded_plugins = manager.load_plugins()
        assert len(loaded_plugins) > 0

        plugin = loaded_plugins[0]
        plugin_class_name = plugin.__class__.__name__

        # Get plugin by class name (how it's stored)
        retrieved_plugin = manager.get_plugin(plugin_class_name)
        assert retrieved_plugin is not None
        assert retrieved_plugin is plugin

        # Disable plugin
        assert manager.disable_plugin(plugin_class_name) is True
        assert plugin.enabled is False

        # Enable plugin
        assert manager.enable_plugin(plugin_class_name) is True
        assert plugin.enabled is True

        # Unload plugin
        assert manager.unload_plugin(plugin_class_name) is True
        assert manager.get_plugin(plugin_class_name) is None

    def test_plugin_search_integration(self, manager):
        """Test plugin search functionality."""
        loaded_plugins = manager.load_plugins()

        # Find ExamplePlugin by class name
        example_plugin = None
        for plugin in loaded_plugins:
            if plugin.__class__.__name__ == "ExamplePlugin":
                example_plugin = plugin
                break

        assert example_plugin is not None

        # Add a recent file
        test_file = __file__
        example_plugin.add_recent_file(test_file)

        # Search for it
        filename = Path(test_file).name
        results = example_plugin.search(filename, {})

        assert len(results) > 0
        assert results[0]["name"] == filename

    def test_plugin_config_integration(self, config_manager):
        """Test plugin configuration management."""
        config_manager.get = Mock(return_value={"max_recent_files": 50})
        config_manager.set = Mock(return_value=None)
        config_manager.save = Mock(return_value=None)

        manager = PluginManager(config_manager)

        # Load plugins
        loaded_plugins = manager.load_plugins()

        # Set config for a plugin
        plugin_name = loaded_plugins[0].__class__.__name__
        new_config = {"test_key": "test_value"}

        assert manager.set_plugin_config(plugin_name, new_config) is True
        config_manager.set.assert_called_with(f"plugins.{plugin_name}", new_config)
        config_manager.save.assert_called()

    def test_plugin_error_isolation(self, manager):
        """Test that plugin errors don't crash the system."""

        # Mock _load_plugin to fail for one plugin
        original_load = manager._load_plugin

        def failing_load(plugin_class, config):
            if plugin_class.__name__ == "ExamplePlugin":
                # Make ExamplePlugin fail
                raise Exception("Simulated plugin load failure")
            return original_load(plugin_class, config)

        manager._load_plugin = failing_load

        # Load plugins - should not crash despite failing plugin
        loaded_plugins = manager.load_plugins()

        # Should load 0 plugins since ExamplePlugin fails
        assert len(loaded_plugins) == 0

        # ExamplePlugin should not be loaded
        assert manager.get_plugin("ExamplePlugin") is None

    def test_plugin_status_reporting(self, manager):
        """Test plugin status reporting."""
        manager.load_plugins()

        status = manager.get_plugin_status()

        # Should have status for loaded plugins
        assert len(status) >= 1

        for _plugin_name, plugin_status in status.items():
            if plugin_status["loaded"]:
                assert "enabled" in plugin_status
                assert "name" in plugin_status
                assert "version" in plugin_status
            else:
                assert plugin_status["enabled"] is False
                assert plugin_status["loaded"] is False
