# Configuration Guide

File Search stores its settings as JSON and creates the file with defaults on
first launch. The location is selected by `platformdirs`:

- Windows: `%LOCALAPPDATA%\filesearch\filesearch\config.json`
- macOS: `~/Library/Application Support/filesearch/config.json`
- Linux: `~/.config/filesearch/config.json`

Application logs are stored separately in the corresponding platform log
directory. The exact resolved paths are available from
`ConfigManager.get_config_file_path()` and the application debug log.

## Settings dialog

Open **Settings > Preferences...** (or press `Ctrl+,`) to edit settings. The
dialog contains Search, UI, Performance, Highlighting, and—when a plugin manager
is available—Plugins tabs. **OK** validates and saves changes, **Cancel** restores
the in-memory values from when the dialog opened, and **Reset** restores defaults
after confirmation.

## Canonical schema

The generated configuration currently has this shape:

```json
{
  "search_preferences": {
    "default_search_directory": "/path/to/home",
    "case_sensitive_search": false,
    "include_hidden_files": false,
    "max_search_results": 1000,
    "file_extensions_to_exclude": [".tmp", ".log", ".swp"]
  },
  "ui_preferences": {
    "window_geometry": {
      "x": 100,
      "y": 100,
      "width": 800,
      "height": 600
    },
    "result_font_size": 12,
    "show_file_icons": true,
    "auto_expand_results": false,
    "audio_notification_on_search_complete": false
  },
  "highlighting": {
    "enabled": true,
    "color": "#FFFF99",
    "case_sensitive": false
  },
  "performance_settings": {
    "search_thread_count": 8,
    "enable_search_cache": false,
    "cache_ttl_minutes": 30
  },
  "config_version": "1.0",
  "plugins": {
    "enabled": [],
    "disabled": []
  },
  "recent": {
    "directories": [],
    "searches": [],
    "max_items": 10
  },
  "security": {
    "warn_before_executables": true,
    "allowed_executable_extensions": [],
    "blocked_executable_extensions": []
  },
  "recent_files": {
    "opened_files": [],
    "max_count": 10
  }
}
```

`performance_settings.search_thread_count` defaults to the detected CPU count,
or 4 when it cannot be detected, so its generated value varies by machine. The
Highlighting tab also supports a `highlighting.style` value of `background`,
`outline`, or `underline`; `background` is the fallback until the dialog first
saves that setting.

## Setting reference

### Search preferences

| Key | Type | Default / constraint |
| --- | --- | --- |
| `default_search_directory` | string | User home directory |
| `case_sensitive_search` | boolean | `false` |
| `include_hidden_files` | boolean | `false` |
| `max_search_results` | integer | `1000`; from 1 through 10,000 |
| `file_extensions_to_exclude` | array | `.tmp`, `.log`, and `.swp` |

### UI preferences

| Key | Type | Default / constraint |
| --- | --- | --- |
| `window_geometry` | object | x 100, y 100, width 800, height 600; integer fields |
| `result_font_size` | integer | `12`; from 8 through 72 |
| `show_file_icons` | boolean | `true` |
| `auto_expand_results` | boolean | `false` |
| `audio_notification_on_search_complete` | boolean | `false` |

### Highlighting

| Key | Type | Default / constraint |
| --- | --- | --- |
| `enabled` | boolean | `true` |
| `color` | string | `#FFFF99`; the dialog accepts a hexadecimal color |
| `case_sensitive` | boolean | `false` |
| `style` | string | Implicit `background`; dialog choices are `background`, `outline`, `underline` |

### Performance

| Key | Type | Default / constraint |
| --- | --- | --- |
| `search_thread_count` | integer | CPU count or 4; from 1 through 32 |
| `enable_search_cache` | boolean | `false` |
| `cache_ttl_minutes` | integer | `30`; from 1 through 1,440 |

The remaining sections are application-managed state: plugin enablement,
recent directories and searches, executable-warning preferences, recently
opened files, and the configuration format version.

## Manual editing and recovery

Close File Search before editing the file to avoid racing the file watcher or a
later save. The file must be valid JSON; JSON comments are not supported. On
load, missing keys are merged from the current defaults so older files gain new
settings automatically.

If the JSON syntax is invalid, File Search logs the parse error and replaces the
file with defaults. If a required section or a validated value has the wrong
type or range, loading raises a configuration error instead. Keep a backup before
manual edits if the existing values matter.

## Programmatic access

Use dotted keys through `ConfigManager`:

```python
from filesearch.core.config_manager import ConfigManager

config = ConfigManager()
max_results = config.get("search_preferences.max_search_results")
config.set("search_preferences.max_search_results", 2000)
config.save()
```

Tests and composed application runtimes can inject explicit home, configuration,
and log directories through `ApplicationRuntime`; normal desktop launches use the
platform locations listed above.
