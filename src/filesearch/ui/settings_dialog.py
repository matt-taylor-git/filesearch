"""Settings dialog module — re-exports from the settings package.

All implementation has moved to filesearch.ui.settings.
This file exists for backward compatibility.
"""

from filesearch.ui.settings import SettingsDialog

__all__ = ["SettingsDialog"]
