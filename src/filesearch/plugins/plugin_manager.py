"""Plugin manager module for loading and managing search plugins.

This module provides the PluginManager class that handles plugin discovery,
loading, initialization, and lifecycle management with error isolation.
"""

import importlib.metadata
import importlib.util
import inspect
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Type

from loguru import logger

from filesearch.core.exceptions import PluginError
from filesearch.plugins.plugin_base import PluginDiscovery, SearchPlugin


class PluginManager:
    """Manager for loading and managing search plugins.

    This class handles the complete plugin lifecycle including discovery,
    loading, initialization, configuration, and unloading with proper
    error isolation to prevent one plugin failure from affecting others.
    """

    def __init__(self, config_manager=None):
        """Initialize the plugin manager.

        Args:
            config_manager: Configuration manager instance for plugin configs
        """
        self._plugins: Dict[str, SearchPlugin] = {}
        self._config_manager = config_manager

        # Plugin directories
        self._builtin_dir = Path(__file__).parent / "builtin"
        self._user_dir = Path.home() / ".filesearch" / "plugins"

        logger.debug("PluginManager initialized")

    def load_plugins(self) -> List[SearchPlugin]:
        """Load and initialize all available plugins.

        Returns:
            List of successfully loaded and initialized plugin instances
        """
        logger.info("Starting plugin loading process")

        # Discover plugin classes
        discovered_plugins = self.discover_plugins()
        # Sort by dependencies
        sorted_plugins = self._sort_by_dependencies(discovered_plugins)
        loaded_plugins = []

        for plugin_class, metadata in sorted_plugins:
            try:
                plugin_name = plugin_class.__name__

                # Skip if already loaded
                if plugin_name in self._plugins:
                    logger.debug(f"Plugin {plugin_name} already loaded, skipping")
                    continue

                # Get plugin configuration
                config = self.get_plugin_config(plugin_name)

                # Load and initialize plugin
                plugin = self._load_plugin(plugin_class, config, metadata)
                if plugin:
                    self._plugins[plugin_name] = plugin
                    loaded_plugins.append(plugin)
                    logger.info(f"Successfully loaded plugin: {plugin_name}")

            except Exception as e:
                logger.error(f"Failed to load plugin {plugin_class.__name__}: {e}")
                # Continue with other plugins (error isolation)

        logger.info(f"Plugin loading complete. Loaded {len(loaded_plugins)} plugins")
        return loaded_plugins

    def get_plugin(self, name: str) -> Optional[SearchPlugin]:
        """Get a loaded plugin by name.

        Args:
            name: Plugin name

        Returns:
            Plugin instance if found and loaded, None otherwise
        """
        return self._plugins.get(name)

    def enable_plugin(self, name: str) -> bool:
        """Enable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was enabled, False if not found or already enabled
        """
        plugin = self._plugins.get(name)
        if plugin and not plugin.enabled:
            plugin.enabled = True
            logger.info(f"Enabled plugin: {name}")
            return True
        return False

    def disable_plugin(self, name: str) -> bool:
        """Disable a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was disabled, False if not found or already disabled
        """
        plugin = self._plugins.get(name)
        if plugin and plugin.enabled:
            plugin.enabled = False
            logger.info(f"Disabled plugin: {name}")
            return True
        return False

    def unload_plugin(self, name: str) -> bool:
        """Unload a plugin.

        Args:
            name: Plugin name

        Returns:
            True if plugin was unloaded, False if not found
        """
        plugin = self._plugins.get(name)
        if plugin:
            try:
                plugin.cleanup()
                del self._plugins[name]
                logger.info(f"Unloaded plugin: {name}")
                return True
            except Exception as e:
                logger.error(f"Error unloading plugin {name}: {e}")
                return False
        return False

    def get_plugin_config(self, name: str) -> Dict[str, Any]:
        """Get configuration for a plugin.

        Args:
            name: Plugin name

        Returns:
            Plugin configuration dictionary
        """
        if self._config_manager:
            plugin_config = self._config_manager.get(f"plugins.{name}", {})
            if isinstance(plugin_config, dict):
                return plugin_config
        return {}

    def set_plugin_config(self, name: str, config: Dict[str, Any]) -> bool:
        """Set configuration for a plugin.

        Args:
            name: Plugin name
            config: Configuration dictionary

        Returns:
            True if configuration was set successfully
        """
        try:
            if self._config_manager:
                self._config_manager.set(f"plugins.{name}", config)
                self._config_manager.save()

            # Update running plugin if loaded
            plugin = self._plugins.get(name)
            if plugin:
                plugin.update_config(config)

            logger.debug(f"Updated configuration for plugin: {name}")
            return True
        except Exception as e:
            logger.error(f"Error setting config for plugin {name}: {e}")
            return False

    def discover_plugins(
        self,
    ) -> List[Tuple[Type[SearchPlugin], Optional[Dict[str, Any]]]]:
        """Discover plugin classes from all sources.

        Returns:
            List of tuples (plugin_class, metadata_dict)
        """
        plugin_classes = []

        # Discover from builtin directory
        builtin_plugins = self._discover_from_directory(self._builtin_dir)
        plugin_classes.extend(builtin_plugins)

        # Discover from user directory
        user_plugins = self._discover_from_directory(self._user_dir)
        plugin_classes.extend(user_plugins)

        # Discover from entry points
        entry_plugins = self._discover_from_entry_points()
        plugin_classes.extend(entry_plugins)

        # Remove duplicates
        unique_classes = []
        seen = set()
        for cls, meta in plugin_classes:
            if cls not in seen:
                unique_classes.append((cls, meta))
                seen.add(cls)

        logger.debug(f"Discovered {len(unique_classes)} unique plugin classes")
        return unique_classes

    def _discover_from_entry_points(
        self,
    ) -> List[Tuple[Type[SearchPlugin], Optional[Dict[str, Any]]]]:
        """Discover plugins from Python entry points.

        Returns:
            List of tuples (plugin_class, None) for entry point plugins
        """
        plugins = []
        try:
            entry_points = importlib.metadata.entry_points(group="filesearch.plugins")
            for ep in entry_points:
                try:
                    cls = ep.load()
                    if (
                        inspect.isclass(cls)
                        and issubclass(cls, SearchPlugin)
                        and cls is not SearchPlugin
                    ):
                        plugins.append(
                            (cls, None)
                        )  # Entry points don't have JSON metadata
                        logger.debug(f"Found entry point plugin: {cls.__name__}")
                except Exception as e:
                    logger.error(f"Error loading entry point {ep.name}: {e}")
        except Exception as e:
            logger.warning(f"Entry points not available: {e}")
        return plugins

    def _sort_by_dependencies(
        self, plugins: List[Tuple[Type[SearchPlugin], Optional[Dict[str, Any]]]]
    ) -> List[Tuple[Type[SearchPlugin], Optional[Dict[str, Any]]]]:
        """Sort plugins by dependency order using topological sort.

        Args:
            plugins: List of (class, metadata) tuples

        Returns:
            Sorted list with dependencies first
        """
        # Create name to plugin map
        name_to_plugin = {}
        name_to_deps = {}

        for cls, meta in plugins:
            name = cls.__name__
            name_to_plugin[name] = (cls, meta)
            deps = meta.get("dependencies", []) if meta else []
            name_to_deps[name] = deps

        # Topological sort
        sorted_names = []
        visited = set()
        temp_visited = set()

        def visit(name):
            if name in temp_visited:
                logger.warning(f"Circular dependency detected involving {name}")
                return
            if name in visited:
                return
            temp_visited.add(name)
            for dep in name_to_deps.get(name, []):
                if dep in name_to_plugin:
                    visit(dep)
            temp_visited.remove(name)
            visited.add(name)
            sorted_names.append(name)

        for name in name_to_plugin:
            if name not in visited:
                visit(name)

        # Return in dependency order
        return [name_to_plugin[name] for name in sorted_names]

    def get_loaded_plugins(self) -> List[SearchPlugin]:
        """Get list of currently loaded plugins.

        Returns:
            List of loaded plugin instances
        """
        return list(self._plugins.values())

    def get_plugin_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all plugins.

        Returns:
            Dictionary mapping plugin names to status info
        """
        status = {}
        for name, plugin in self._plugins.items():
            status[name] = {
                "loaded": True,
                "enabled": plugin.enabled,
                "name": plugin.name,
                "version": plugin.version,
                "description": plugin.description,
                "author": plugin.author,
            }

        # Include discovered but not loaded plugins
        for cls, meta in self.discover_plugins():
            name = cls.__name__
            if name not in status:
                status[name] = {
                    "loaded": False,
                    "enabled": False,
                    "name": name,
                    "version": "unknown",
                    "description": "Not loaded",
                    "author": "unknown",
                }

        return status

    def _load_plugin(
        self,
        plugin_class: Type[SearchPlugin],
        config: Dict[str, Any],
        metadata: Optional[Dict[str, Any]] = None,
    ) -> Optional[SearchPlugin]:
        """Load and initialize a single plugin with error isolation.

        Args:
            plugin_class: Plugin class to load
            config: Configuration for the plugin
            metadata: Metadata dictionary from plugin.json

        Returns:
            Initialized plugin instance or None if loading failed
        """
        try:
            # Validate plugin class
            if not PluginDiscovery.is_valid_plugin(plugin_class):
                logger.warning(f"Invalid plugin class: {plugin_class.__name__}")
                return None

            # Check version compatibility
            if metadata:
                min_v = metadata.get("min_app_version", "0.0.0")
                max_v = metadata.get("max_app_version", "999.999.999")
                app_version = "1.0.0"  # TODO: Get from config or version file
                try:
                    if not (min_v <= app_version <= max_v):
                        logger.warning(
                            f"Plugin {plugin_class.__name__} requires app version {min_v} - {max_v}, current {app_version}"
                        )
                        return None
                except TypeError:
                    logger.warning(
                        f"Invalid version format for plugin {plugin_class.__name__}"
                    )

            # Instantiate plugin with metadata
            plugin = plugin_class(metadata)

            # Initialize with configuration
            if plugin.initialize(config):
                return plugin
            else:
                logger.error(f"Plugin {plugin_class.__name__} initialization failed")
                return None

        except Exception as e:
            logger.error(f"Error loading plugin {plugin_class.__name__}: {e}")
            return None

    def _discover_from_directory(
        self, directory: Path
    ) -> List[Tuple[Type[SearchPlugin], Optional[Dict[str, Any]]]]:
        """Discover plugins from a directory.

        Args:
            directory: Directory to scan for plugins

        Returns:
            List of tuples (plugin_class, metadata_dict)
        """
        plugin_classes = []

        if not directory.exists():
            logger.debug(f"Plugin directory does not exist: {directory}")
            return plugin_classes

        try:
            # Scan for Python files
            for file_path in directory.glob("*.py"):
                if file_path.name.startswith("_"):
                    continue  # Skip private modules

                try:
                    # Import the module
                    module_name = file_path.stem
                    spec = importlib.util.spec_from_file_location(
                        module_name, file_path
                    )
                    if spec and spec.loader:
                        module = importlib.util.module_from_spec(spec)
                        spec.loader.exec_module(module)

                        # Find plugin classes in the module
                        for name, obj in inspect.getmembers(module):
                            if (
                                inspect.isclass(obj)
                                and issubclass(obj, SearchPlugin)
                                and obj is not SearchPlugin
                            ):
                                plugin_classes.append(obj)
                                logger.debug(
                                    f"Found plugin class {obj.__name__} in {file_path}"
                                )

                except Exception as e:
                    logger.error(f"Error loading plugin from {file_path}: {e}")
                    continue  # Continue with other files

        except Exception as e:
            logger.error(f"Error scanning plugin directory {directory}: {e}")

        # Load metadata if available
        metadata = None
        metadata_path = directory / "plugin.json"
        if metadata_path.exists():
            try:
                with open(metadata_path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
                logger.debug(f"Loaded metadata from {metadata_path}")
            except Exception as e:
                logger.error(f"Error loading metadata from {metadata_path}: {e}")

        # Assign metadata to all plugins in this directory
        result = [(cls, metadata) for cls in plugin_classes]
        return result
