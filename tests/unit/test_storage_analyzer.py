"""Unit tests for storage analysis."""

from collections import namedtuple
from pathlib import Path
from unittest.mock import patch

import pytest

from filesearch.core.config_manager import ConfigManager
from filesearch.core.storage_analyzer import StorageAnalyzer


@pytest.fixture
def config_manager(tmp_path):
    """Create an isolated config manager for storage tests."""
    with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
        manager = ConfigManager(app_name="storage-test")
        yield manager


class TestStorageAnalyzer:
    """Focused tests for directory-size aggregation."""

    def test_aggregates_nested_directory_sizes(self, tmp_path, config_manager):
        """Nested folders contribute to the root total."""
        docs = tmp_path / "docs"
        media = tmp_path / "media"
        docs.mkdir()
        media.mkdir()

        (tmp_path / "top.txt").write_bytes(b"a" * 5)
        (docs / "report.txt").write_bytes(b"b" * 10)
        (media / "clip.mp4").write_bytes(b"c" * 7)

        analyzer = StorageAnalyzer(config_manager)
        result = analyzer.analyze(tmp_path)

        assert result.summary.total_size == 22
        assert result.summary.item_count == 5
        assert {child.name: child.size for child in result.root.children} == {
            "docs": 10,
            "media": 7,
            "top.txt": 5,
        }

    def test_handles_empty_and_single_file_roots(self, tmp_path, config_manager):
        """Empty directories and one-file directories both analyze cleanly."""
        empty_root = tmp_path / "empty"
        empty_root.mkdir()

        analyzer = StorageAnalyzer(config_manager)
        empty_result = analyzer.analyze(empty_root)
        assert empty_result.summary.total_size == 0
        assert empty_result.summary.item_count == 0

        single_root = tmp_path / "single"
        single_root.mkdir()
        (single_root / "only.bin").write_bytes(b"x" * 12)

        single_result = analyzer.analyze(single_root)
        assert single_result.summary.total_size == 12
        assert single_result.summary.item_count == 1
        assert single_result.root.children[0].name == "only.bin"

    def test_skips_unreadable_directories_without_aborting(
        self, tmp_path, config_manager, monkeypatch
    ):
        """Permission failures increment skipped counts but keep scanning."""
        blocked = tmp_path / "blocked"
        blocked.mkdir()
        (tmp_path / "visible.txt").write_bytes(b"x" * 9)

        original_scandir = __import__("os").scandir

        def fake_scandir(path):
            if Path(path) == blocked:
                raise PermissionError("denied")
            return original_scandir(path)

        monkeypatch.setattr("filesearch.core.storage_analyzer.os.scandir", fake_scandir)

        analyzer = StorageAnalyzer(config_manager)
        result = analyzer.analyze(tmp_path)

        assert result.summary.total_size == 9
        assert result.summary.skipped_count >= 1

    def test_avoids_symlink_directory_loops(self, tmp_path, config_manager):
        """Symlinked directories are skipped instead of recursively looping."""
        nested = tmp_path / "nested"
        nested.mkdir()
        (nested / "data.bin").write_bytes(b"x" * 6)

        loop = nested / "loop"
        try:
            loop.symlink_to(tmp_path, target_is_directory=True)
        except (OSError, NotImplementedError):
            pytest.skip("Symlinks are not available in this environment")

        analyzer = StorageAnalyzer(config_manager)
        result = analyzer.analyze(tmp_path)

        assert result.summary.total_size == 6
        assert result.summary.skipped_count >= 1

    def test_hidden_filter_tracks_existing_config_behavior(self, tmp_path, config_manager):
        """Dot-hidden names follow the shared include_hidden_files preference."""
        (tmp_path / ".secret.txt").write_bytes(b"a" * 4)
        (tmp_path / "visible.txt").write_bytes(b"b" * 3)

        analyzer = StorageAnalyzer(config_manager)
        hidden_excluded = analyzer.analyze(tmp_path)
        assert hidden_excluded.summary.total_size == 3

        config_manager.set("search_preferences.include_hidden_files", True)
        analyzer = StorageAnalyzer(config_manager)
        hidden_included = analyzer.analyze(tmp_path)
        assert hidden_included.summary.total_size == 7

    def test_reports_drive_totals_from_disk_usage(self, tmp_path, config_manager, monkeypatch):
        """Drive summary values come from shutil.disk_usage for the selected root."""
        (tmp_path / "visible.txt").write_bytes(b"x" * 5)
        disk_usage = namedtuple("usage", "total used free")(300, 180, 120)
        monkeypatch.setattr(
            "filesearch.core.storage_analyzer.shutil.disk_usage",
            lambda path: disk_usage,
        )

        analyzer = StorageAnalyzer(config_manager)
        result = analyzer.analyze(tmp_path)

        assert result.summary.drive_total == 300
        assert result.summary.drive_used == 180
        assert result.summary.drive_free == 120
