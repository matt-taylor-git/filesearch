# Plugin Development Guide

## Overview

The File Search application supports a plugin architecture that allows extending functionality without modifying the core codebase. Plugins can add new search capabilities, integrate with external services, or provide specialized file processing.

## Plugin Architecture

### Core Components

- **Plugin Manager**: Loads and manages plugin lifecycle
- **Plugin Base Class**: Abstract interface all plugins must implement
- **Discovery Mechanisms**: Directory scanning, Python entry points, and user-defined locations
- **Configuration System**: Plugin-specific settings integrated with main config

### Plugin Types

1. **Search Plugins**: Extend search functionality (e.g., recent files, cloud storage)
2. **Processor Plugins**: Modify or filter search results
3. **UI Plugins**: Add new interface components

## Developing a Plugin

### Basic Structure

Create a Python package with your plugin class inheriting from `SearchPlugin`:

```python
from filesearch.plugins.plugin_base import SearchPlugin

class MyPlugin(SearchPlugin):
    def __init__(self, metadata=None):
        super().__init__(metadata)

    def initialize(self, config):
        # Setup your plugin
        return True

    def search(self, query, context):
        # Implement search logic
        return [{'path': '/path/to/file', 'name': 'file.txt', 'source': self.name}]

    def get_name(self):
        return "My Plugin"
```

### Plugin Metadata

Create a `plugin.json` file in your plugin directory:

```json
{
  "name": "My Plugin",
  "version": "1.0.0",
  "author": "Your Name",
  "description": "Description of what your plugin does",
  "dependencies": [],
  "min_app_version": "1.0.0",
  "max_app_version": "2.0.0",
  "config_schema": {
    "api_key": {
      "type": "string",
      "description": "API key for service"
    }
  }
}
```

### Installation

1. **Directory Installation**: Place plugin files in `~/.filesearch/plugins/`
2. **Entry Point Installation**: Use setuptools entry points in `setup.py`:

```python
setup(
    name="my-plugin",
    entry_points={
        'filesearch.plugins': [
            'my_plugin = my_plugin_module:MyPlugin',
        ],
    },
)
```

## API Reference

### SearchPlugin Methods

- `initialize(config: Dict) -> bool`: Initialize with configuration
- `search(query: str, context: Dict) -> List[Dict]`: Perform search
- `get_name() -> str`: Return plugin name
- `cleanup()`: Clean up resources

### Context Dictionary

The `context` parameter in `search()` contains:
- `directory`: Search root directory
- `max_results`: Maximum results to return
- `query`: Original search query

### Result Format

Search results should be dictionaries with:
- `path`: File path (string)
- `name`: Display name
- `source`: Plugin name
- `size`: File size in bytes (optional)
- `modified`: Modification timestamp (optional)

## Best Practices

1. **Error Handling**: Always handle exceptions gracefully
2. **Performance**: Avoid blocking operations in search methods
3. **Configuration**: Validate config in `initialize()`
4. **Dependencies**: Specify plugin dependencies in metadata
5. **Versioning**: Check app version compatibility
6. **Logging**: Use the provided logger for debugging

## Example: Recent Files Plugin

See `src/filesearch/plugins/builtin/example_plugin.py` for a complete example implementation.

## Testing

Write unit tests for your plugin following the existing patterns in `tests/unit/test_example_plugin.py`.

## Distribution

Package your plugin as a Python package and distribute via PyPI, or provide as a directory for manual installation.
