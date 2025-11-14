"""Configuration manager module for handling user preferences.

This module provides the ConfigManager class for loading, saving, and managing
application configuration using JSON format with cross-platform directory support.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional

import platformdirs
from loguru import logger

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
        
        # Define default configuration values
        self._defaults: Dict[str, Any] = {
            "search": {
                "max_results": 1000,
                "max_workers": 4,
                "case_sensitive": False,
                "include_hidden": False
            },
            "ui": {
                "window_width": 800,
                "window_height": 600,
                "theme": "light",
                "font_size": 12
            },
            "performance": {
                "cache_enabled": True,
                "cache_size_mb": 100,
                "thread_pool_size": 4
            },
            "plugins": {
                "enabled": [],
                "disabled": []
            },
            "recent": {
                "directories": [],
                "searches": [],
                "max_items": 10
            }
        }
        
        logger.debug(f"ConfigManager initialized with config_dir={self.config_dir}")
        
        # Auto-create config with defaults if it doesn't exist
        if not self.config_file.exists():
            self._create_default_config()
        
        # Load configuration on initialization
        self.load()
    
    def _create_default_config(self) -> None:
        """Create default configuration file if it doesn't exist."""
        try:
            # Create config directory if it doesn't exist
            self.config_dir.mkdir(parents=True, exist_ok=True)
            
            # Create config file with default values
            with open(self.config_file, 'w', encoding='utf-8') as f:
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
            if '.' in key:
                keys = key.split('.')
                value = self._config
                
                for k in keys:
                    if isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        # Return default if key not found
                        logger.debug(f"Config key not found: {key}, using default: {default}")
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
            if '.' in key:
                keys = key.split('.')
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
            with open(self.config_file, 'w', encoding='utf-8') as f:
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
                logger.warning(f"Config file not found at {self.config_file}, creating defaults")
                self._create_default_config()
            
            # Load configuration from file
            with open(self.config_file, 'r', encoding='utf-8') as f:
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
        def deep_merge(defaults: Dict[str, Any], loaded: Dict[str, Any]) -> Dict[str, Any]:
            result = defaults.copy()
            
            for key, value in loaded.items():
                if key in result and isinstance(result[key], dict) and isinstance(value, dict):
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
            required_sections = ["search", "ui", "performance"]
            for section in required_sections:
                if section not in self._config:
                    raise ConfigError(f"Missing required configuration section: {section}")
            
            # Validate search section
            search_config = self._config.get("search", {})
            if not isinstance(search_config.get("max_results"), int):
                raise ConfigError("search.max_results must be an integer")
            
            if not isinstance(search_config.get("max_workers"), int):
                raise ConfigError("search.max_workers must be an integer")
            
            # Validate UI section
            ui_config = self._config.get("ui", {})
            if not isinstance(ui_config.get("window_width"), int):
                raise ConfigError("ui.window_width must be an integer")
            
            if not isinstance(ui_config.get("window_height"), int):
                raise ConfigError("ui.window_height must be an integer")
            
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


# Convenience function for quick config access
def get_config(app_name: str = "filesearch", app_author: str = "filesearch") -> ConfigManager:
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