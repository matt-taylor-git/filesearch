"""UI tests for the storage visualization tab."""

from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QApplication, QScrollArea

from filesearch.core.config_manager import ConfigManager
from filesearch.ui.storage_tab import StorageTabWidget


@pytest.fixture(scope="session")
def qapp():
    """Create QApplication instance for UI tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def config_manager(tmp_path):
    """Create an isolated config manager for UI tests."""
    with patch("platformdirs.user_config_dir", return_value=str(tmp_path)):
        manager = ConfigManager(app_name="storage-ui-test")
        yield manager


@pytest.fixture
def storage_tab(qapp, qtbot, config_manager, tmp_path):
    """Create a storage tab rooted at a temp directory."""
    widget = StorageTabWidget(config_manager, tmp_path)
    widget.resize(1280, 900)
    widget.show()
    qtbot.addWidget(widget)
    return widget


class TestStorageTabWidget:
    """Exercise refresh, drill-down, and hover state."""

    def test_refresh_runs_background_scan(self, storage_tab, qtbot, tmp_path):
        """Refreshing populates analysis data and shows scan status."""
        (tmp_path / "alpha.txt").write_bytes(b"a" * 8)

        storage_tab.set_root_path(tmp_path, refresh=True)
        qtbot.waitUntil(storage_tab.has_analysis, timeout=5000)

        assert storage_tab._analysis_result is not None
        assert "Scanned" in storage_tab._status_label.text()
        assert storage_tab._treemap_stack.currentWidget() == storage_tab._treemap

    def test_breadcrumb_drilldown_updates_visible_root(
        self, storage_tab, qtbot, tmp_path
    ):
        """Opening a child directory updates the breadcrumb chain."""
        child = tmp_path / "projects"
        child.mkdir()
        (child / "notes.txt").write_bytes(b"x" * 6)

        storage_tab.set_root_path(tmp_path, refresh=True)
        qtbot.waitUntil(storage_tab.has_analysis, timeout=5000)

        storage_tab._show_node(child)

        assert storage_tab._current_node is not None
        assert storage_tab._current_node.path == child
        button_texts = []
        for index in range(storage_tab._breadcrumb_layout.count()):
            item = storage_tab._breadcrumb_layout.itemAt(index)
            widget = item.widget()
            if widget is not None and hasattr(widget, "text"):
                button_texts.append(widget.text().strip())
        assert "projects" in button_texts

    def test_treemap_includes_nested_descendants(self, storage_tab, qtbot, tmp_path):
        """The treemap should paint nested descendants, not only top-level folders."""
        alpha = tmp_path / "alpha"
        beta = alpha / "beta"
        gamma = tmp_path / "gamma"
        beta.mkdir(parents=True)
        gamma.mkdir()
        (beta / "deep.bin").write_bytes(b"x" * 4096)
        (gamma / "wide.bin").write_bytes(b"y" * 2048)

        storage_tab.set_root_path(tmp_path, refresh=True)
        qtbot.waitUntil(storage_tab.has_analysis, timeout=5000)

        visible_paths = {tile.node.path for tile in storage_tab._treemap._tiles}
        assert beta in visible_paths

    def test_storage_page_uses_scroll_area(self, storage_tab):
        """The storage page should be wrapped in a scroll area for overflow."""
        assert storage_tab.findChild(QScrollArea) is not None
