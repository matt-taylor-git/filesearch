"""Configuration manager module for handling user preferences.

This module provides the ConfigManager class for loading, saving, and managing
application configuration using JSON format with cross-platform directory support.
"""

import json
import os
from pathlib import Path
from typing import Any, Callable, Dict, Optional

import platformdirs
from loguru import logger

try:
    from PyQt6.QtCore import QFileSystemWatcher, QObject
    from PyQt6.QtWidgets import QApplication

    QT_AVAILABLE = True
except ImportError:
    QT_AVAILABLE = False
    QFileSystemWatcher = None
    QObject = object

from filesearch.core.exceptions import ConfigError


class ConfigManager:
    """Configuration manager for loading and saving user preferences.

    This class provides a centralized way to manage application configuration
    using JSON format with automatic cross-platform directory detection.

    Attributes:
        app_name (str): Application name for config directory
        app_author (str): Application author for config directory
        config_dir (Path): Configuration directory path
        config_file (Path): Configuration file path
        _config (Dict[str, Any]): In-memory configuration cache
        _defaults (Dict[str, Any]): Default configuration values
    """

    def __init__(self, app_name: str = "filesearch", app_author: str = "filesearch"):
        """Initialize the configuration manager.

        Args:
            app_name: Application name (default: "filesearch")
            app_author: Application author (default: "filesearch")
        """
        self.app_name = app_name
        self.app_author = app_author

        # Use platformdirs for cross-platform config directory detection
        self.config_dir = Path(platformdirs.user_config_dir(app_name, app_author))
        self.config_file = self.config_dir / "config.json"

        # Initialize configuration cache
        self._config: Dict[str, Any] = {}

        # Define default configuration values matching AC requirements
        self._defaults: Dict[str, Any] = {
            "search_preferences": {
                "default_search_directory": str(Path.home()),
                "case_sensitive_search": False,
                "include_hidden_files": False,
                "max_search_results": 1000,
                "file_extensions_to_exclude": [".tmp", ".log", ".swp"],
            },
            "ui_preferences": {
                "window_geometry": {"x": 100, "y": 100, "width": 800, "height": 600},
                "result_font_size": 12,
                "show_file_icons": True,
                "auto_expand_results": False,
                "audio_notification_on_search_complete": False,
            },
            "performance_settings": {
                "search_thread_count": os.cpu_count() or 4,
                "enable_search_cache": False,
                "cache_ttl_minutes": 30,
            },
            "config_version": "1.0",
            "plugins": {"enabled": [], "disabled": []},
            "recent": {"directories": [], "searches": [], "max_items": 10},
        }

        # File watcher for auto-reload (optional, requires PyQt6)
        self._file_watcher: Optional[QFileSystemWatcher] = None
        self._reload_callbacks: list[Callable] = []

        logger.debug(f"ConfigManager initialized with config_dir={self.config_dir}")

        # Auto-create config with defaults if it doesn't exist
        if not self.config_file.exists():
            self._create_default_config()

        # Load configuration on initialization
        self.load()

        # Setup file watcher for auto-reload if Qt is available
        if QT_AVAILABLE:
            self._setup_file_watcher()

    def _create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Create config file with default values
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._defaults, f, indent=2, ensure_ascii=False)

            logger.info(f"Created default configuration at {self.config_file}")

        except OSError as e:
            logger.error(f"Error creating config directory or file: {e}")
            raise ConfigError(f"Cannot create configuration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error creating default config: {e}")
            raise ConfigError(f"Error creating default configuration: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """Get a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "search.max_results")
            default: Default value to return if key not found

        Returns:
            Configuration value or default if not found

        Example:
            >>> max_results = config.get("search.max_results", 1000)
            >>> theme = config.get("ui.theme", "light")
        """
        try:
            # Handle dot notation for nested keys
            if "." in key:
                keys = key.split(".")
                value = self._config

                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        # Return default if key not found
                        logger.debug(
                            f"Config key not found: {key}, using default: {default}"
                        )
                        return default

                logger.debug(f"Retrieved config value for {key}: {value}")
                return value

            # Simple key lookup
            if key in self._config:
                value = self._config[key]
                logger.debug(f"Retrieved config value for {key}: {value}")
                return value

            # Return default if key not found
            logger.debug(f"Config key not found: {key}, using default: {default}")
            return default

        except Exception as e:
            logger.error(f"Error getting config value for {key}: {e}")
            return default

    def set(self, key: str, value: Any) -> None:
        """Set a configuration value.

        Args:
            key: Configuration key (supports dot notation, e.g., "search.max_results")
            value: Value to set

        Example:
            >>> config.set("search.max_results", 2000)
            >>> config.set("ui.theme", "dark")
        """
        try:
            # Handle dot notation for nested keys
            if "." in key:
                keys = key.split(".")
                config = self._config

                # Navigate to the parent dict
                for k in keys[:-1]:
                    if k not in config:
                        config[k] = {}
                    config = config[k]

                # Set the value
                config[keys[-1]] = value
            else:
                # Simple key set
                self._config[key] = value

            logger.debug(f"Set config value for {key}: {value}")

        except Exception as e:
            logger.error(f"Error setting config value for {key}: {e}")
            raise ConfigError(f"Cannot set configuration value: {e}")

    def save(self) -> None:
        """Save the current configuration to file.

        Raises:
            ConfigError: If configuration cannot be saved
        """
        try:
            # Validate configuration before saving
            self._validate_config()

            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)

            # Save configuration to file
            with open(self.config_file, "w", encoding="utf-8") as f:
                json.dump(self._config, f, indent=2, ensure_ascii=False)

            logger.info(f"Configuration saved to {self.config_file}")

        except OSError as e:
            logger.error(f"Error saving configuration: {e}")
            raise ConfigError(f"Cannot save configuration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error saving configuration: {e}")
            raise ConfigError(f"Error saving configuration: {e}")

    def load(self) -> None:
        """Load configuration from file.

        If the config file doesn't exist or is invalid, creates default config.

        Raises:
            ConfigError: If configuration cannot be loaded
        """
        try:
            if not self.config_file.exists():
                logger.warning(
                    f"Config file not found at {self.config_file}, creating defaults"
                )
                self._create_default_config()

            # Load configuration from file
            with open(self.config_file, "r", encoding="utf-8") as f:
                loaded_config = json.load(f)

            # Merge with defaults to ensure all keys exist
            self._config = self._merge_with_defaults(loaded_config)

            # Validate loaded configuration
            self._validate_config()

            logger.info(f"Configuration loaded from {self.config_file}")

        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON in config file: {e}")
            # Create default config if file is corrupted
            self._create_default_config()
            self.load()
        except OSError as e:
            logger.error(f"Error loading configuration: {e}")
            raise ConfigError(f"Cannot load configuration: {e}")
        except Exception as e:
            logger.error(f"Unexpected error loading configuration: {e}")
            raise ConfigError(f"Error loading configuration: {e}")

    def _merge_with_defaults(self, loaded_config: Dict[str, Any]) -> Dict[str, Any]:
        """Merge loaded configuration with default values.

        Args:
            loaded_config: Configuration loaded from file

        Returns:
            Merged configuration with defaults
        """

        def deep_merge(
            defaults: Dict[str, Any], loaded: Dict[str, Any]
        ) -> Dict[str, Any]:
            result = defaults.copy()

            for key, value in loaded.items():
                if (
                    key in result
                    and isinstance(result[key], dict)
                    and isinstance(value, dict)
                ):
                    result[key] = deep_merge(result[key], value)
                else:
                    result[key] = value

            return result

        return deep_merge(self._defaults, loaded_config)

    def _validate_config(self) -> None:
        """Validate the current configuration.

        Raises:
            ConfigError: If configuration is invalid
        """
        try:
            # Check required sections exist
            required_sections = [
                "search_preferences",
                "ui_preferences",
                "performance_settings",
            ]
            for section in required_sections:
                if section not in self._config:
                    raise ConfigError(
                        f"Missing required configuration section: {section}"
                    )

            # Validate search_preferences section
            search_prefs = self._config.get("search_preferences", {})
            if not isinstance(search_prefs.get("max_search_results"), int):
                raise ConfigError(
                    "search_preferences.max_search_results must be an integer"
                )

            max_results = search_prefs.get("max_search_results", 1000)
            if max_results < 1 or max_results > 10000:
                raise ConfigError(
                    "search_preferences.max_search_results must be between 1 and 10000"
                )

            if not isinstance(search_prefs.get("case_sensitive_search"), bool):
                raise ConfigError(
                    "search_preferences.case_sensitive_search must be a boolean"
                )

            if not isinstance(search_prefs.get("include_hidden_files"), bool):
                raise ConfigError(
                    "search_preferences.include_hidden_files must be a boolean"
                )

            if not isinstance(search_prefs.get("file_extensions_to_exclude"), list):
                raise ConfigError(
                    "search_preferences.file_extensions_to_exclude must be a list"
                )

            # Validate ui_preferences section
            ui_prefs = self._config.get("ui_preferences", {})
            if not isinstance(ui_prefs.get("result_font_size"), int):
                raise ConfigError("ui_preferences.result_font_size must be an integer")

            font_size = ui_prefs.get("result_font_size", 12)
            if font_size < 8 or font_size > 72:
                raise ConfigError(
                    "ui_preferences.result_font_size must be between 8 and 72"
                )

            if not isinstance(ui_prefs.get("show_file_icons"), bool):
                raise ConfigError("ui_preferences.show_file_icons must be a boolean")

            if not isinstance(ui_prefs.get("auto_expand_results"), bool):
                raise ConfigError(
                    "ui_preferences.auto_expand_results must be a boolean"
                )

            # Validate window_geometry
            window_geom = ui_prefs.get("window_geometry", {})
            if not isinstance(window_geom.get("x"), int):
                raise ConfigError("ui_preferences.window_geometry.x must be an integer")
            if not isinstance(window_geom.get("y"), int):
                raise ConfigError("ui_preferences.window_geometry.y must be an integer")
            if not isinstance(window_geom.get("width"), int):
                raise ConfigError(
                    "ui_preferences.window_geometry.width must be an integer"
                )
            if not isinstance(window_geom.get("height"), int):
                raise ConfigError(
                    "ui_preferences.window_geometry.height must be an integer"
                )

            # Validate performance_settings section
            perf_settings = self._config.get("performance_settings", {})
            if not isinstance(perf_settings.get("search_thread_count"), int):
                raise ConfigError(
                    "performance_settings.search_thread_count must be an integer"
                )

            thread_count = perf_settings.get("search_thread_count", 4)
            if thread_count < 1 or thread_count > 32:
                raise ConfigError(
                    "performance_settings.search_thread_count must be between 1 and 32"
                )

            if not isinstance(perf_settings.get("enable_search_cache"), bool):
                raise ConfigError(
                    "performance_settings.enable_search_cache must be a boolean"
                )

            if not isinstance(perf_settings.get("cache_ttl_minutes"), int):
                raise ConfigError(
                    "performance_settings.cache_ttl_minutes must be an integer"
                )

            cache_ttl = perf_settings.get("cache_ttl_minutes", 30)
            if cache_ttl < 1 or cache_ttl > 1440:  # Max 24 hours
                raise ConfigError(
                    "performance_settings.cache_ttl_minutes must be between 1 and 1440"
                )

            logger.debug("Configuration validation passed")

        except ConfigError:
            raise
        except Exception as e:
            logger.error(f"Configuration validation failed: {e}")
            raise ConfigError(f"Invalid configuration: {e}")

    def get_all(self) -> Dict[str, Any]:
        """Get the entire configuration dictionary.

        Returns:
            Complete configuration dictionary
        """
        return self._config.copy()

    def reset_to_defaults(self) -> None:
        """Reset configuration to default values."""
        self._config = self._defaults.copy()
        logger.info("Configuration reset to defaults")

    def get_config_file_path(self) -> Path:
        """Get the configuration file path.

        Returns:
            Path to the configuration file
        """
        return self.config_file

    def get_config_dir(self) -> Path:
        """Get the configuration directory path.

        Returns:
            Path to the configuration directory
        """
        return self.config_dir

    def _setup_file_watcher(self) -> None:
        """Setup file watcher for auto-reload functionality."""
        try:
            if not QT_AVAILABLE or not QApplication.instance():
                logger.debug(
                    "Qt not available or no QApplication instance, "
                    "skipping file watcher setup"
                )
                return

            self._file_watcher = QFileSystemWatcher()
            self._file_watcher.fileChanged.connect(self._on_config_file_changed)

            # Add config file to watcher
            if self.config_file.exists():
                self._file_watcher.addPath(str(self.config_file))
                logger.debug(f"File watcher setup for {self.config_file}")
            else:
                logger.warning(
                    f"Config file does not exist, cannot setup file watcher: "
                    f"{self.config_file}"
                )

        except Exception as e:
            logger.error(f"Error setting up file watcher: {e}")
            self._file_watcher = None

    def _on_config_file_changed(self, path: str) -> None:
        """Handle config file changes for auto-reload."""
        try:
            logger.info(f"Config file changed: {path}, reloading configuration")
            self.load()

            # Notify registered callbacks
            for callback in self._reload_callbacks:
                try:
                    callback()
                except Exception as e:
                    logger.error(f"Error in config reload callback: {e}")

        except Exception as e:
            logger.error(f"Error reloading configuration after file change: {e}")

    def add_reload_callback(self, callback: Callable) -> None:
        """Add a callback to be called when configuration is reloaded.

        Args:
            callback: Function to call when config is reloaded
        """
        if callback not in self._reload_callbacks:
            self._reload_callbacks.append(callback)
            logger.debug(f"Added reload callback: {callback}")

    def remove_reload_callback(self, callback: Callable) -> None:
        """Remove a reload callback.

        Args:
            callback: Callback function to remove
        """
        if callback in self._reload_callbacks:
            self._reload_callbacks.remove(callback)
            logger.debug(f"Removed reload callback: {callback}")


# Convenience function for quick config access
def get_config(
    app_name: str = "filesearch", app_author: str = "filesearch"
) -> ConfigManager:
    """Get a ConfigManager instance.

    Args:
        app_name: Application name
        app_author: Application author

    Returns:
        ConfigManager instance

    Example:
        >>> config = get_config()
        >>> max_results = config.get("search.max_results")
    """
    return ConfigManager(app_name, app_author)
