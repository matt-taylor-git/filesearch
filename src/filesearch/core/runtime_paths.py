"""Runtime path helpers for source and frozen application builds."""

from __future__ import annotations

import sys
from importlib import resources
from pathlib import Path

import platformdirs

from filesearch import APP_AUTHOR, APP_INTERNAL_NAME


def is_frozen() -> bool:
    """Return whether the app is running from a bundled executable."""
    return bool(getattr(sys, "frozen", False))


def get_resource_path(*parts: str) -> Path:
    """Resolve a package resource path in source and PyInstaller bundles."""
    if hasattr(sys, "_MEIPASS"):
        return Path(sys._MEIPASS) / "filesearch" / Path(*parts)

    return Path(resources.files("filesearch").joinpath(*parts))


def get_app_icon_path() -> Path:
    """Return the bundled PNG icon used at runtime."""
    return get_resource_path("resources", "icons", "app_icon.png")


def get_log_dir(
    app_name: str = APP_INTERNAL_NAME, app_author: str = APP_AUTHOR
) -> Path:
    """Return the user log directory for the application."""
    return Path(platformdirs.user_log_dir(app_name, app_author))


def ensure_log_dir(
    app_name: str = APP_INTERNAL_NAME, app_author: str = APP_AUTHOR
) -> Path:
    """Create and return the application log directory."""
    log_dir = get_log_dir(app_name, app_author)
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir
