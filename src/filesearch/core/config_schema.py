"""Static configuration schema reference for File Search."""

from __future__ import annotations

CONFIG_SCHEMA = {
    "_comment": "File Search configuration schema reference",
    "version": "1.0.0",
    "search": {
        "case_sensitive": False,
        "include_hidden": False,
        "max_results": 10000,
        "file_extensions_to_exclude": [],
    },
    "ui": {
        "window_width": 800,
        "window_height": 600,
        "results_font_size": 12,
        "show_file_icons": True,
        "auto_expand_results": False,
    },
    "highlighting": {
        "enabled": True,
        "color": "#FFFF99",
        "case_sensitive": False,
        "style": "background",
    },
    "performance": {
        "search_thread_count": 4,
        "enable_search_cache": False,
        "cache_ttl_minutes": 30,
    },
    "plugins": {"enabled": []},
}
