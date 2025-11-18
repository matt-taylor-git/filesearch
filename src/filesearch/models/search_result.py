from dataclasses import dataclass
from pathlib import Path
from typing import Optional


@dataclass
class SearchResult:
    """Represents a single search result"""

    path: Path  # File/folder path
    size: int  # File size in bytes (0 for directories)
    modified: float  # Modification timestamp
    plugin_source: Optional[str] = None  # Plugin name if from plugin

    def get_display_name(self) -> str:
        """Return filename for display"""
        return self.path.name

    def get_display_path(self) -> str:
        """Return path with user directory abbreviated"""
        try:
            return str(self.path.relative_to(Path.home()))
        except ValueError:
            return str(self.path)

    def get_display_size(self) -> str:
        """Return human-readable file size"""
        if self.size == 0:
            return "Folder"

        size = float(self.size)
        for unit in ["B", "KiB", "MiB", "GiB"]:
            if size < 1024.0:
                return "{:.1f} {}".format(size, unit)
            size /= 1024.0
        return "{:.1f} TiB".format(size)

    def get_display_date(self) -> str:
        """Return formatted modification date"""
        from datetime import datetime

        return datetime.fromtimestamp(self.modified).strftime("%b %d, %Y")

    @property
    def filename(self) -> str:
        """Return the filename (convenience property)."""
        return self.path.name

    @property
    def is_directory(self) -> bool:
        """Check if the result is a directory (convenience property)."""
        return self.path.is_dir()
