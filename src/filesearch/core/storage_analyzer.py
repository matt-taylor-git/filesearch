"""Storage analysis for disk-usage visualization."""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Optional

from loguru import logger

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import SearchError
from filesearch.models.storage_node import (
    StorageAnalysisResult,
    StorageNode,
    StorageSummary,
)

ProgressCallback = Callable[[str, int, int], None]


@dataclass
class _AnalysisCounters:
    """Mutable counters for a storage analysis run."""

    item_count: int = 0
    skipped_count: int = 0
    progress_events: int = 0


class StorageAnalyzer:
    """Analyze a directory tree into aggregate storage metrics."""

    def __init__(self, config_manager: Optional[ConfigManager] = None) -> None:
        self.config_manager = config_manager
        self.include_hidden = False
        if config_manager is not None:
            self.include_hidden = config_manager.get(
                "search_preferences.include_hidden_files", False
            )
        self._cancelled = False

    def cancel(self) -> None:
        """Cancel the current analysis."""
        self._cancelled = True

    def is_cancelled(self) -> bool:
        """Return whether cancellation has been requested."""
        return self._cancelled

    def analyze(
        self,
        root_path: Path,
        progress_callback: Optional[ProgressCallback] = None,
    ) -> StorageAnalysisResult:
        """Analyze *root_path* recursively."""
        self._cancelled = False
        path = Path(root_path)

        if not path.exists():
            raise SearchError("Directory does not exist", path=str(path))
        if not path.is_dir():
            raise SearchError("Storage analysis requires a directory", path=str(path))

        logger.info(f"Starting storage analysis for {path}")
        counters = _AnalysisCounters()
        root_node = self._scan_directory(path, counters, progress_callback)

        if self._cancelled:
            raise SearchError("Storage analysis cancelled", path=str(path))

        usage = shutil.disk_usage(path)
        summary = StorageSummary(
            root_path=path,
            total_size=root_node.size,
            drive_total=usage.total,
            drive_used=usage.used,
            drive_free=usage.free,
            item_count=counters.item_count,
            skipped_count=counters.skipped_count,
        )
        logger.info(
            "Storage analysis complete for {}: {} items, {} skipped".format(
                path, counters.item_count, counters.skipped_count
            )
        )
        return StorageAnalysisResult(root=root_node, summary=summary)

    def _scan_directory(
        self,
        directory: Path,
        counters: _AnalysisCounters,
        progress_callback: Optional[ProgressCallback],
    ) -> StorageNode:
        """Recursively build a storage tree for *directory*."""
        total_size = 0
        children: list[StorageNode] = []

        try:
            with os.scandir(directory) as entries:
                sorted_entries = sorted(entries, key=lambda entry: entry.name.lower())
        except (OSError, PermissionError) as exc:
            counters.skipped_count += 1
            logger.warning(f"Cannot access directory {directory}: {exc}")
            return StorageNode(path=directory, size=0, is_dir=True, children=[])

        for entry in sorted_entries:
            if self._cancelled:
                break

            if not self.include_hidden and entry.name.startswith("."):
                continue

            entry_path = Path(entry.path)

            try:
                if entry.is_symlink():
                    if entry.is_dir(follow_symlinks=True):
                        counters.skipped_count += 1
                        logger.debug(f"Skipping symlinked directory {entry_path}")
                        continue

                    child = self._scan_file_entry(entry, entry_path)
                elif entry.is_dir(follow_symlinks=False):
                    child = self._scan_directory(
                        entry_path, counters, progress_callback
                    )
                else:
                    child = self._scan_file_entry(entry, entry_path)
            except (OSError, PermissionError) as exc:
                counters.skipped_count += 1
                logger.warning(f"Skipping unreadable path {entry_path}: {exc}")
                continue

            counters.item_count += 1
            total_size += child.size
            children.append(child)
            self._emit_progress(entry_path, counters, progress_callback)

        children.sort(key=lambda node: (-node.size, node.name.lower()))
        return StorageNode(
            path=directory, size=total_size, is_dir=True, children=children
        )

    def _scan_file_entry(self, entry: os.DirEntry, path: Path) -> StorageNode:
        """Create a node from a file-like directory entry."""
        try:
            size = entry.stat(follow_symlinks=True).st_size
        except OSError:
            size = entry.stat(follow_symlinks=False).st_size
        return StorageNode(path=path, size=size, is_dir=False, children=[])

    def _emit_progress(
        self,
        path: Path,
        counters: _AnalysisCounters,
        progress_callback: Optional[ProgressCallback],
    ) -> None:
        """Throttle progress notifications to keep the UI readable."""
        if progress_callback is None:
            return

        counters.progress_events += 1
        if counters.progress_events == 1 or counters.progress_events % 25 == 0:
            progress_callback(str(path), counters.item_count, counters.skipped_count)
