"""Data models for storage analysis and treemap visualization."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path


def format_bytes(size_bytes: int) -> str:
    """Return a human-readable byte count."""
    if size_bytes <= 0:
        return "0 B"

    size = float(size_bytes)
    for unit in ["B", "KiB", "MiB", "GiB"]:
        if size < 1024.0:
            return "{:.1f} {}".format(size, unit)
        size /= 1024.0
    return "{:.1f} TiB".format(size)


@dataclass(slots=True)
class StorageNode:
    """Represents a file-system node within a storage tree."""

    path: Path
    size: int
    is_dir: bool
    children: list["StorageNode"] = field(default_factory=list)

    @property
    def name(self) -> str:
        """Return the label shown for this node."""
        if self.path.name:
            return self.path.name
        if self.path.drive:
            return self.path.drive
        return str(self.path)

    def get_display_size(self) -> str:
        """Return the node's size in human-readable format."""
        return format_bytes(self.size)


@dataclass(slots=True)
class StorageSummary:
    """Summary metrics for a storage analysis run."""

    root_path: Path
    total_size: int
    drive_total: int
    drive_used: int
    drive_free: int
    item_count: int
    skipped_count: int


@dataclass(slots=True)
class StorageAnalysisResult:
    """Complete storage analysis result."""

    root: StorageNode
    summary: StorageSummary
