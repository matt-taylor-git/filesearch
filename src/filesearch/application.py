"""Production application composition helpers."""

from pathlib import Path

import platformdirs

from filesearch import APP_AUTHOR, APP_INTERNAL_NAME
from filesearch.core.application_runtime import ApplicationRuntime
from filesearch.ui.desktop_effects import QtDesktopEffects


def create_system_runtime() -> ApplicationRuntime:
    """Create the runtime boundary backed by the current user environment."""
    return ApplicationRuntime(
        home_dir=Path.home(),
        config_dir=Path(platformdirs.user_config_dir(APP_INTERNAL_NAME, APP_AUTHOR)),
        log_dir=Path(platformdirs.user_log_dir(APP_INTERNAL_NAME, APP_AUTHOR)),
        desktop_effects=QtDesktopEffects(),
    )
