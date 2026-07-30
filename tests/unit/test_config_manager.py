"""Unit tests for the configuration manager module."""

import json
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, mock_open, patch  # noqa: F401

import pytest

from filesearch.core.config_manager import ConfigManager, get_config
from filesearch.core.exceptions import ConfigError


class TestConfigManager:
    """Test cases for ConfigManager class."""

    @pytest.fixture
    def temp_config_dir(self, application_runtime):
        """Create a temporary config directory."""
        return application_runtime.config_dir

    @pytest.fixture
    def config_manager(self, application_runtime):
        """Create a ConfigManager instance with temporary directory."""
        return ConfigManager(
            app_name="testapp",
            app_author="testauthor",
            runtime=application_runtime,
            watch_config=False,
        )

    def test_init_default_values(self, temp_config_dir, application_runtime):
        """Test initialization with default values."""
        manager = ConfigManager(runtime=application_runtime, watch_config=False)

        assert manager.app_name == "filesearch"
        assert manager.app_author == "filesearch"
        assert manager.config_dir == temp_config_dir
        assert manager.config_file == temp_config_dir / "config.json"
        assert manager._config != {}

    def test_init_custom_values(self, application_runtime):
        """Test initialization with custom values."""
        manager = ConfigManager(
            app_name="customapp",
            app_author="customauthor",
            runtime=application_runtime,
            watch_config=False,
        )

        assert manager.app_name == "customapp"
        assert manager.app_author == "customauthor"

    def test_create_default_config(self, application_runtime):
        """Test creating default configuration."""
        manager = ConfigManager(runtime=application_runtime, watch_config=False)

        assert manager.config_file.exists()
        assert manager.config_file.is_file()

        # Verify default config content
        with open(manager.config_file) as f:
            config_data = json.load(f)

        assert "search_preferences" in config_data
        assert "ui_preferences" in config_data
        assert "performance_settings" in config_data
        assert "plugins" in config_data
        assert "recent" in config_data
        assert "config_version" in config_data

    def test_get_simple_key(self, config_manager):
        """Test getting a simple configuration key."""
        value = config_manager.get("search_preferences.max_search_results")
        assert isinstance(value, int)
        assert value > 0

    def test_get_nested_key(self, config_manager):
        """Test getting a nested configuration key."""
        value = config_manager.get("ui_preferences.result_font_size")
        assert isinstance(value, int)
        assert value == 12

    def test_get_with_default(self, config_manager):
        """Test getting a key with default value."""
        value = config_manager.get("nonexistent.key", "default_value")
        assert value == "default_value"

    def test_get_nonexistent_key_no_default(self, config_manager):
        """Test getting a non-existent key without default."""
        value = config_manager.get("nonexistent.key")
        assert value is None

    def test_set_simple_key(self, config_manager):
        """Test setting a simple configuration key."""
        config_manager.set("test_key", "test_value")
        assert config_manager.get("test_key") == "test_value"

    def test_set_nested_key(self, config_manager):
        """Test setting a nested configuration key."""
        config_manager.set("test.nested.key", "nested_value")
        assert config_manager.get("test.nested.key") == "nested_value"

    def test_set_overwrites_existing(self, config_manager):
        """Test that set overwrites existing values."""
        original_value = config_manager.get("search_preferences.max_search_results")
        config_manager.set("search_preferences.max_search_results", 9999)
        assert config_manager.get("search_preferences.max_search_results") == 9999
        assert (
            config_manager.get("search_preferences.max_search_results")
            != original_value
        )

    def test_save_and_load(self, config_manager):
        """Test saving and loading configuration."""
        # Set a custom value
        config_manager.set("test.save_load", "test_value")

        # Save configuration
        config_manager.save()

        # Create new manager instance (should load saved config)
        new_manager = ConfigManager(runtime=config_manager.runtime, watch_config=False)
        assert new_manager.get("test.save_load") == "test_value"

    def test_load_merges_with_defaults(self, temp_config_dir, application_runtime):
        """Test that load merges user config with defaults."""
        # Create a partial config file
        config_file = temp_config_dir / "config.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)

        partial_config = {"search_preferences": {"max_search_results": 500}}

        with open(config_file, "w") as f:
            json.dump(partial_config, f)

        manager = ConfigManager(runtime=application_runtime, watch_config=False)

        assert manager.get("search_preferences.max_search_results") == 500

        # Should have default values for missing keys
        assert manager.get("performance_settings.search_thread_count") is not None
        assert manager.get("ui_preferences.show_file_icons") is True

    def test_load_invalid_json(self, temp_config_dir, application_runtime):
        """Test loading invalid JSON configuration."""
        config_file = temp_config_dir / "config.json"
        temp_config_dir.mkdir(parents=True, exist_ok=True)

        # Write invalid JSON
        with open(config_file, "w") as f:
            f.write("{invalid json}")

        manager = ConfigManager(runtime=application_runtime, watch_config=False)
        assert manager.config_file.exists()
        assert manager.get("search_preferences.max_search_results") == 1000

    def test_validate_config_valid(self, config_manager):
        """Test configuration validation with valid config."""
        # Should not raise exception
        config_manager._validate_config()

    def test_validate_config_missing_section(self, config_manager):
        """Test configuration validation with missing required section."""
        # Remove required section
        del config_manager._config["search_preferences"]

        with pytest.raises(ConfigError, match="Missing required configuration section"):
            config_manager._validate_config()

    def test_validate_config_invalid_type(self, config_manager):
        """Test configuration validation with invalid type."""
        # Set invalid type
        config_manager._config["search_preferences"]["max_search_results"] = (
            "not_an_int"
        )

        with pytest.raises(
            ConfigError,
            match=r"search_preferences\.max_search_results must be an integer",
        ):
            config_manager._validate_config()

    def test_get_all(self, config_manager):
        """Test getting entire configuration."""
        all_config = config_manager.get_all()

        assert isinstance(all_config, dict)
        assert "search_preferences" in all_config
        assert "ui_preferences" in all_config
        assert all_config == config_manager._config

        # Verify it's a copy
        all_config["test"] = "value"
        assert "test" not in config_manager._config

    def test_reset_to_defaults(self, config_manager):
        """Test resetting configuration to defaults."""
        # Modify config
        config_manager.set("search_preferences.max_search_results", 9999)
        assert config_manager.get("search_preferences.max_search_results") == 9999

        # Reset to defaults
        config_manager.reset_to_defaults()
        assert config_manager.get("search_preferences.max_search_results") == 1000

    def test_get_config_file_path(self, config_manager):
        """Test getting configuration file path."""
        path = config_manager.get_config_file_path()
        assert path == config_manager.config_file
        assert isinstance(path, Path)

    def test_get_config_dir(self, config_manager):
        """Test getting configuration directory path."""
        path = config_manager.get_config_dir()
        assert path == config_manager.config_dir
        assert isinstance(path, Path)

    def test_save_creates_directory(self, temp_config_dir, application_runtime):
        """Test that save creates config directory if it doesn't exist."""
        # Use a non-existent directory
        new_dir = temp_config_dir / "new_config_dir"

        runtime = replace(application_runtime, config_dir=new_dir)
        manager = ConfigManager(runtime=runtime, watch_config=False)
        manager.set("test.key", "value")
        manager.save()

        assert new_dir.exists()
        assert manager.config_file.exists()


class TestGetConfigFunction:
    """Test cases for get_config convenience function."""

    def test_get_config_function(self, application_runtime):
        """Test get_config convenience function."""
        config = get_config(runtime=application_runtime, watch_config=False)

        assert isinstance(config, ConfigManager)
        assert config.app_name == "filesearch"

    def test_get_config_with_custom_params(self, application_runtime):
        """Test get_config with custom parameters."""
        config = get_config(
            app_name="custom",
            app_author="custom",
            runtime=application_runtime,
            watch_config=False,
        )

        assert isinstance(config, ConfigManager)
        assert config.app_name == "custom"
        assert config.app_author == "custom"
