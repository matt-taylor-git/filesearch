# Configuration Guide

This document describes the configuration system for the File Search application, including all available settings, their default values, and how to configure them.

## Overview

File Search uses a JSON-based configuration system with cross-platform support. Configuration is automatically stored in platform-appropriate locations:

- **Windows**: `%APPDATA%\filesearch\config.json`
- **macOS**: `~/Library/Application Support/filesearch/config.json`
- **Linux**: `~/.config/filesearch/config.json`

The configuration file is automatically created on first launch with sensible defaults. You can manually edit the JSON file, but it's recommended to use the built-in Settings dialog for safety.

## Configuration Structure

The configuration is organized into three main sections:

1. **Search Preferences** - Controls search behavior and filters
2. **UI Preferences** - Controls user interface appearance and layout
3. **Performance Settings** - Controls performance-related options

## Search Preferences

### `default_search_directory`
- **Type**: String (path)
- **Default**: User's home directory
- **Description**: The default directory to search in when the application starts

### `case_sensitive_search`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether file searches should be case-sensitive

### `include_hidden_files`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether to include hidden files (starting with `.`) in search results

### `max_search_results`
- **Type**: Integer
- **Default**: `1000`
- **Range**: 1-10000
- **Description**: Maximum number of search results to return

### `file_extensions_to_exclude`
- **Type**: Array of strings
- **Default**: `[".tmp", ".log", ".swp"]`
- **Description**: List of file extensions to exclude from search results

**Example:**
```json
"search_preferences": {
  "default_search_directory": "/home/user/documents",
  "case_sensitive_search": false,
  "include_hidden_files": false,
  "max_search_results": 1000,
  "file_extensions_to_exclude": [".tmp", ".log", ".swp", ".bak"]
}
```

## UI Preferences

## Highlighting Settings

Controls how search result highlighting appears in the results list.

### `enabled`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Whether search result highlighting is enabled
- **Note**: Disabling can improve performance on slower systems

### `color`
- **Type**: String (hex color code)
- **Default**: `"#FFFF99"` (light yellow)
- **Description**: Color used to highlight matching text in search results
- **Example**: `"#90EE90"` (light green), `"#FFB6C1"` (light pink)

### `case_sensitive`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether highlighting matching should be case-sensitive
- **Note**: This is independent of the search case sensitivity setting

### `style`
- **Type**: String
- **Default**: `"background"`
- **Options**: `"background"`, `"outline"`, `"underline"`
- **Description**: Style of highlighting applied to matching text
- **Examples**:
  - `"background"`: Fills matching text with highlight color
  - `"outline"`: Draws a rectangle around matching text
  - `"underline"`: Draws a line under matching text

**Example:**
```json
"highlighting": {
  "enabled": true,
  "color": "#FFFF99",
  "case_sensitive": false,
  "style": "background"
}
```

## UI Preferences

### `window_geometry`
- **Type**: Object with x, y, width, height
- **Default**: `{"x": 100, "y": 100, "width": 800, "height": 600}`
- **Description**: Window position and size

### `result_font_size`
- **Type**: Integer
- **Default**: `12`
- **Range**: 8-72
- **Description**: Font size for search results in points

### `show_file_icons`
- **Type**: Boolean
- **Default**: `true`
- **Description**: Whether to show file icons in results

### `auto_expand_results`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether to automatically expand result categories

**Example:**
```json
"ui_preferences": {
  "window_geometry": {
    "x": 100,
    "y": 100,
    "width": 800,
    "height": 600
  },
  "result_font_size": 12,
  "show_file_icons": true,
  "auto_expand_results": false
}
```

## Performance Settings

### `search_thread_count`
- **Type**: Integer
- **Default**: Number of CPU cores
- **Range**: 1-32
- **Description**: Number of threads to use for parallel searching

### `enable_search_cache`
- **Type**: Boolean
- **Default**: `false`
- **Description**: Whether to enable search result caching (for future use)

### `cache_ttl_minutes`
- **Type**: Integer
- **Default**: `30`
- **Range**: 1-1440 (24 hours)
- **Description**: Time-to-live for cached search results in minutes

**Example:**
```json
"performance_settings": {
  "search_thread_count": 4,
  "enable_search_cache": false,
  "cache_ttl_minutes": 30
}
```

## Manual Configuration Editing

You can manually edit the configuration file, but be aware of the following:

1. **Validation**: The configuration is validated on load. Invalid values will be replaced with defaults.
2. **Comments**: JSON doesn't support comments, but you can add them as long as you don't use the Settings dialog (which will strip them on save).
3. **Backup**: Make a backup before manual editing in case of syntax errors.

### Example Complete Configuration File

```json
{
  "config_version": "1.0",
  "search_preferences": {
    "default_search_directory": "/home/user/documents",
    "case_sensitive_search": false,
    "include_hidden_files": false,
    "max_search_results": 1000,
    "file_extensions_to_exclude": [
      ".tmp",
      ".log",
      ".swp",
      ".bak",
      ".cache"
    ]
  },
  "ui_preferences": {
    "window_geometry": {
      "x": 200,
      "y": 150,
      "width": 1000,
      "height": 700
    },
    "result_font_size": 14,
    "show_file_icons": true,
    "auto_expand_results": false
  },
  "performance_settings": {
    "search_thread_count": 8,
    "enable_search_cache": false,
    "cache_ttl_minutes": 30
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
```

## Using the Settings Dialog

The easiest way to configure the application is through the built-in Settings dialog:

1. Open the **Settings** menu
2. Select **Preferences...** (or press `Ctrl+,`)
3. Navigate through the tabs to configure different aspects:
   - **Search**: Configure search behavior and filters
   - **UI**: Configure appearance and layout
   - **Performance**: Configure performance-related options
   - **Highlighting**: Configure search result highlighting appearance
4. Click **Apply** or **OK** to save changes
5. Click **Reset** to restore default values

### Real-time Validation

The Settings dialog provides real-time validation:

- Invalid values are highlighted
- Range limits are enforced
- Required fields are validated
- Changes apply immediately without restart (where possible)

## Configuration Versioning

The configuration includes a `config_version` field for future migrations. When new versions of the application introduce configuration changes, this helps ensure smooth upgrades.

## Troubleshooting

### Configuration Not Loading

If the configuration fails to load:

1. Check JSON syntax using a validator
2. Ensure all required sections exist
3. Verify value types match the specification
4. Check file permissions

### Settings Not Saving

If settings don't persist:

1. Verify the config directory is writable
2. Check disk space
3. Look for error messages in the application log
4. Try resetting to defaults

### Invalid Values

If you see validation errors:

1. Check that values are within allowed ranges
2. Verify data types (boolean, integer, string, array)
3. Ensure required fields are present
4. Use the Settings dialog for safe editing

## Programmatic Access

You can access configuration values programmatically:

```python
from filesearch.core.config_manager import ConfigManager

# Get config manager instance
config = ConfigManager()

# Get values
max_results = config.get("search_preferences.max_search_results")
case_sensitive = config.get("search_preferences.case_sensitive_search")

# Set values
config.set("search_preferences.max_search_results", 2000)
config.set("ui_preferences.result_font_size", 16)

# Save changes
config.save()
```

## Environment-Specific Configuration

For different environments (development, testing, production), you can:

1. Use different configuration files
2. Override settings via environment variables
3. Use command-line arguments (when implemented)

## Security Considerations

- Configuration files may contain sensitive paths
- File permissions should restrict access to the user
- Avoid storing passwords or API keys in configuration
- Validate all user input before saving to configuration
