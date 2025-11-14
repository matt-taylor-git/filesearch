"""Plugin base module defining the abstract base class for search plugins.

This module provides the SearchPlugin abstract base class that all search plugins
must inherit from, along with plugin metadata and discovery mechanisms.
"""

import inspect
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any, Dict, List, Optional

from loguru import logger

from filesearch.core.exceptions import PluginError


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
    
    def __init__(self):
        """Initialize the plugin with default metadata."""
        self._name: str = self.__class__.__name__
        self._version: str = "1.0.0"
        self._author: str = "Unknown"
        self._description: str = "No description provided"
        self._config: Dict[str, Any] = {}
        self._enabled: bool = True
        
        logger.debug(f"Plugin initialized: {self._name}")
    
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
    def config(self) -> Dict[str, Any]:
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
    def initialize(self, config: Dict[str, Any]) -> bool:
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
    def search(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
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
    
    def update_config(self, config: Dict[str, Any]) -> bool:
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
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """Validate plugin configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if configuration is valid, False otherwise
            
        Note:
            Subclasses should override this to provide custom validation.
        """
        return True
    
    def get_metadata(self) -> Dict[str, Any]:
        """Get plugin metadata.
        
        Returns:
            Dictionary containing plugin metadata
        """
        return {
            'name': self._name,
            'version': self._version,
            'author': self._author,
            'description': self._description,
            'enabled': self._enabled,
            'config': self._config.copy()
        }


class PluginDiscovery:
    """Plugin discovery and loading utility.
    
    This class provides methods for discovering and loading search plugins
    from various sources including directory scanning and entry points.
    """
    
    @staticmethod
    def discover_from_directory(plugin_dir: Path) -> List[type]:
        """Discover plugins from a directory.
        
        Args:
            plugin_dir: Directory to search for plugins
            
        Returns:
            List of plugin classes found
        """
        plugins = []
        
        if not plugin_dir.exists():
            logger.warning(f"Plugin directory does not exist: {plugin_dir}")
            return plugins
        
        try:
            # Scan for Python files in the plugin directory
            for file_path in plugin_dir.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue  # Skip private modules
                
                # This is a simplified discovery mechanism
                # In a real implementation, you might use importlib
                logger.debug(f"Found potential plugin file: {file_path}")
            
        except Exception as e:
            logger.error(f"Error discovering plugins from directory {plugin_dir}: {e}")
        
        return plugins
    
    @staticmethod
    def is_valid_plugin(cls) -> bool:
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
                if hasattr(method, '__isabstractmethod__') and method.__isabstractmethod__:
                    abstract_methods.append(name)
            
            if abstract_methods:
                logger.warning(f"Plugin {cls.__name__} missing abstract methods: {abstract_methods}")
                return False
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating plugin {cls}: {e}")
            return False
    
    @staticmethod
    def load_plugin(plugin_class: type, config: Dict[str, Any] = None) -> Optional[SearchPlugin]:
        """Load and initialize a plugin.
        
        Args:
            plugin_class: Plugin class to instantiate
            config: Configuration dictionary for the plugin
            
        Returns:
            Initialized plugin instance or None if loading failed
        """
        try:
            if config is None:
                config = {}
            
            # Instantiate the plugin
            plugin = plugin_class()
            
            # Initialize with configuration
            if plugin.initialize(config):
                logger.info(f"Successfully loaded plugin: {plugin.get_name()}")
                return plugin
            else:
                logger.error(f"Failed to initialize plugin: {plugin_class.__name__}")
                return None
                
        except Exception as e:
            logger.error(f"Error loading plugin {plugin_class}: {e}")
            return None


# Example plugin implementation for reference
class ExamplePlugin(SearchPlugin):
    """Example plugin demonstrating the plugin interface.
    
    This is a simple example plugin that searches for files
    based on file size criteria.
    """
    
    def __init__(self):
        """Initialize the example plugin."""
        super().__init__()
        self._name = "Example Size Filter"
        self._version = "1.0.0"
        self._author = "FileSearch Team"
        self._description = "Filters search results by file size"
    
    def initialize(self, config: Dict[str, Any]) -> bool:
        """Initialize the example plugin.
        
        Args:
            config: Configuration dictionary
            
        Returns:
            True if initialization successful
        """
        try:
            self._config = config
            
            # Validate required config
            if 'min_size' not in config and 'max_size' not in config:
                logger.warning("ExamplePlugin: No size filters specified")
            
            logger.info("ExamplePlugin initialized successfully")
            return True
            
        except Exception as e:
            logger.error(f"ExamplePlugin initialization failed: {e}")
            return False
    
    def search(self, query: str, context: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Perform size-based search filtering.
        
        Args:
            query: Search query (not used in this example)
            context: Search context
            
        Returns:
            List of filtered results
        """
        # This is a simplified example
        # In a real plugin, you would implement actual search logic
        results = []
        
        try:
            # Get search parameters from context
            directory = context.get('directory', '.')
            min_size = self._config.get('min_size', 0)
            max_size = self._config.get('max_size', float('inf'))
            
            logger.debug(f"ExamplePlugin searching in {directory} with size filter")
            
            # Example search logic (simplified)
            # In reality, you would scan files and filter by size
            
        except Exception as e:
            logger.error(f"ExamplePlugin search failed: {e}")
            raise PluginError(f"ExamplePlugin search error: {e}")
        
        return results
    
    def get_name(self) -> str:
        """Get plugin name.
        
        Returns:
            Plugin name
        """
        return self._name