"""Plugin base module defining the abstract base class for search plugins.

This module provides the SearchPlugin abstract base class that all search plugins
must inherit from, along with plugin metadata and class validation.
"""

import inspect
from abc import ABC, abstractmethod
from typing import Any

from loguru import logger


class SearchPlugin(ABC):
    """Abstract base class for all search plugins.

    This class defines the interface that all search plugins must implement.
    Plugins provide specialized search capabilities beyond the core file search.

    Attributes:
        _name (str): Plugin name
        _version (str): Plugin version
        _author (str): Plugin author
        _description (str): Plugin description
        _config (Dict[str, Any]): Plugin configuration
        _enabled (bool): Whether plugin is enabled
    """

    def __init__(self, metadata: dict[str, Any] | None = None):
        """Initialize the plugin with default metadata."""
        self._name: str = self.__class__.__name__
        self._version: str = "1.0.0"
        self._author: str = "Unknown"
        self._description: str = "No description provided"
        self._config: dict[str, Any] = {}
        self._enabled: bool = True
        self._metadata: dict[str, Any] = {}

        if metadata:
            self._load_metadata(metadata)

        logger.debug(f"Plugin initialized: {self._name}")

    def _load_metadata(self, metadata: dict[str, Any]) -> None:
        """Load metadata from dictionary.

        Args:
            metadata: Metadata dictionary from plugin.json
        """
        self._name = metadata.get("name", self._name)
        self._version = metadata.get("version", self._version)
        self._author = metadata.get("author", self._author)
        self._description = metadata.get("description", self._description)
        self._metadata = metadata

    @property
    def name(self) -> str:
        """Get plugin name.

        Returns:
            Plugin name
        """
        return self._name

    @property
    def version(self) -> str:
        """Get plugin version.

        Returns:
            Plugin version
        """
        return self._version

    @property
    def author(self) -> str:
        """Get plugin author.

        Returns:
            Plugin author
        """
        return self._author

    @property
    def description(self) -> str:
        """Get plugin description.

        Returns:
            Plugin description
        """
        return self._description

    @property
    def dependencies(self) -> list[str]:
        """Get plugin dependencies.

        Returns:
            List of plugin names this plugin depends on
        """
        return self._metadata.get("dependencies", [])

    @property
    def config(self) -> dict[str, Any]:
        """Get plugin configuration.

        Returns:
            Plugin configuration dictionary
        """
        return self._config.copy()

    @property
    def enabled(self) -> bool:
        """Check if plugin is enabled.

        Returns:
            True if plugin is enabled, False otherwise
        """
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        """Set plugin enabled state.

        Args:
            value: True to enable, False to disable
        """
        self._enabled = bool(value)
        logger.debug(f"Plugin {self._name} enabled set to: {self._enabled}")

    @abstractmethod
    def initialize(self, config: dict[str, Any]) -> bool:
        """Initialize the plugin with configuration.

        Args:
            config: Configuration dictionary for the plugin

        Returns:
            True if initialization successful, False otherwise

        Raises:
            PluginError: If initialization fails

        Note:
            This method must be implemented by all plugin subclasses.
            It should validate the configuration and prepare the plugin for use.
        """
        pass

    @abstractmethod
    def search(self, query: str, context: dict[str, Any]) -> list[dict[str, Any]]:
        """Perform a search using this plugin.

        Args:
            query: Search query string
            context: Search context dictionary containing additional information
                    such as search directory, file types, etc.

        Returns:
            List of search results, where each result is a dictionary
            containing at least 'path', 'name', and 'type' keys

        Raises:
            PluginError: If search fails

        Note:
            This method must be implemented by all plugin subclasses.
            The context dictionary may contain:
            - 'directory': Search directory path
            - 'file_types': List of file types to search
            - 'max_results': Maximum number of results
            - 'case_sensitive': Whether search is case sensitive
        """
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get the plugin name.

        Returns:
            Plugin name

        Note:
            This method must be implemented by all plugin subclasses.
            It should return a user-friendly name for the plugin.
        """
        pass

    def get_version(self) -> str:
        """Get the plugin version.

        Returns:
            Plugin version string

        Note:
            This method can be overridden by subclasses to provide
            dynamic version information.
        """
        return self._version

    def cleanup(self) -> None:
        """Clean up plugin resources.

        This method is called when the plugin is being unloaded.
        Subclasses should override this to release any resources.
        """
        logger.debug(f"Cleaning up plugin: {self._name}")

    def update_config(self, config: dict[str, Any]) -> bool:
        """Update plugin configuration.

        Args:
            config: New configuration dictionary

        Returns:
            True if update successful, False otherwise
        """
        try:
            self._config.update(config)
            logger.debug(f"Updated config for plugin {self._name}: {config}")
            return True
        except Exception as e:
            logger.error(f"Error updating config for plugin {self._name}: {e}")
            return False

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate plugin configuration.

        Args:
            config: Configuration dictionary to validate

        Returns:
            True if configuration is valid, False otherwise

        Note:
            Subclasses should override this to provide custom validation.
        """
        return True

    def get_metadata(self) -> dict[str, Any]:
        """Get plugin metadata.

        Returns:
            Dictionary containing plugin metadata
        """
        return {
            "name": self._name,
            "version": self._version,
            "author": self._author,
            "description": self._description,
            "enabled": self._enabled,
            "config": self._config.copy(),
        }


class PluginDiscovery:
    """Validate plugin classes before the manager loads them."""

    @staticmethod
    def is_valid_plugin(cls: type[object]) -> bool:
        """Check if a class is a valid plugin.

        Args:
            cls: Class to check

        Returns:
            True if class is a valid plugin, False otherwise
        """
        try:
            # Check if it's a class
            if not inspect.isclass(cls):
                return False

            # Check if it's a subclass of SearchPlugin
            if not issubclass(cls, SearchPlugin):
                return False

            # Check if it's not the abstract base class itself
            if cls is SearchPlugin:
                return False

            # Check if all abstract methods are implemented
            abstract_methods = []
            for name, method in inspect.getmembers(cls, inspect.isfunction):
                if (
                    hasattr(method, "__isabstractmethod__")
                    and method.__isabstractmethod__
                ):
                    abstract_methods.append(name)

            if abstract_methods:
                logger.warning(
                    f"Plugin {cls.__name__} missing abstract methods: "
                    f"{abstract_methods}"
                )
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating plugin {cls}: {e}")
            return False
