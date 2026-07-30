"""Integration tests for the plugin system."""

from pathlib import Path
from typing import Any

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

    def test_plugin_search_integration(
        self, manager: PluginManager, tmp_path: Path
    ) -> None:
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
        test_file = tmp_path / "recent-notes.txt"
        test_file.write_text("notes", encoding="utf-8")
        example_plugin.add_recent_file(str(test_file))

        # Search for it
        filename = test_file.name
        results = example_plugin.search(filename, {})

        assert len(results) > 0
        assert results[0]["name"] == filename

    def test_plugin_config_integration(self, config_manager: ConfigManager) -> None:
        """Test plugin configuration management."""
        manager = PluginManager(config_manager)

        # Load plugins
        loaded_plugins = manager.load_plugins()

        # Set config for a plugin
        plugin_name = loaded_plugins[0].__class__.__name__
        new_config = {"test_key": "test_value"}

        assert manager.set_plugin_config(plugin_name, new_config) is True
        assert manager.get_plugin_config(plugin_name) == new_config

        reloaded_config = ConfigManager(
            runtime=config_manager.runtime, watch_config=False
        )
        assert (
            PluginManager(reloaded_config).get_plugin_config(plugin_name) == new_config
        )

    def test_plugin_error_isolation(
        self, manager: PluginManager, application_runtime: Any
    ) -> None:
        """A failing user plugin does not prevent a healthy plugin from loading."""
        plugin_dir = application_runtime.home_dir / ".filesearch" / "plugins"
        plugin_dir.mkdir(parents=True)
        (plugin_dir / "broken_plugin.py").write_text(
            """from typing import Any

from filesearch.plugins.plugin_base import SearchPlugin

class BrokenPlugin(SearchPlugin):
    def initialize(self, config: dict[str, Any]) -> bool:
        raise RuntimeError("simulated initialization failure")

    def search(self, query: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        return []

    def get_name(self) -> str:
        return "Broken"
""",
            encoding="utf-8",
        )

        loaded_plugins = manager.load_plugins()

        assert manager.get_plugin("BrokenPlugin") is None
        assert manager.get_plugin("ExamplePlugin") in loaded_plugins

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
