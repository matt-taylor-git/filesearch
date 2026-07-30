"""Tests for the application runtime composition boundary."""

from pathlib import Path

from filesearch.core.application_runtime import ApplicationRuntime
from filesearch.core.config_manager import ConfigManager
from filesearch.plugins.plugin_manager import PluginManager


class RecordingDesktopEffects:
    """Minimal test double supplied through the public runtime boundary."""


def test_runtime_composes_temporary_home_config_and_plugin_locations(tmp_path):
    """Runtime paths keep application state beneath test-owned directories."""
    home_dir = tmp_path / "home"
    config_dir = tmp_path / "config"
    log_dir = tmp_path / "logs"
    effects = RecordingDesktopEffects()
    runtime = ApplicationRuntime(
        home_dir=home_dir,
        config_dir=config_dir,
        log_dir=log_dir,
        desktop_effects=effects,
    )

    manager = ConfigManager(runtime=runtime, watch_config=False)
    plugins = PluginManager(manager)

    assert manager.config_file == config_dir / "config.json"
    assert manager.get("search_preferences.default_search_directory") == str(home_dir)
    assert plugins._user_dir == home_dir / ".filesearch" / "plugins"
    assert runtime.desktop_effects is effects
