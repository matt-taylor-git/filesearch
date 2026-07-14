"""Unit tests for the sidebar widget."""

from pathlib import Path
from unittest.mock import patch

import pytest
from PyQt6.QtWidgets import QApplication, QLabel, QProgressBar

from filesearch.core.file_utils import DriveUsage
from filesearch.ui.sidebar_widget import SidebarWidget


@pytest.fixture
def app():
    """Create QApplication for testing."""
    if not QApplication.instance():
        app = QApplication([])
    else:
        app = QApplication.instance()
    yield app


@pytest.fixture
def widget(app, qtbot):
    """Create a SidebarWidget instance for testing."""
    sidebar = SidebarWidget()
    sidebar.show()
    qtbot.addWidget(sidebar)
    return sidebar


class TestSidebarWidgetLocations:
    """Tests for custom folder controls in the sidebar."""

    def test_browse_action_exists(self, widget):
        """The sidebar exposes a choose-folder action in locations."""
        assert widget._browse_button is not None
        assert widget._browse_button.text().strip() == "Choose Folder..."
        assert widget._browse_button.isVisible()

    def test_custom_location_row_appears(self, widget):
        """Setting a custom folder shows a dedicated location row."""
        custom_path = Path.home() / "Projects"

        widget.set_custom_location(custom_path)

        assert widget._custom_location_button is not None
        assert widget._custom_location_button.isVisible()
        assert widget._custom_location_button.toolTip() == str(custom_path)
        assert widget.get_custom_location() == custom_path
        assert widget._custom_location_button.text().strip() == custom_path.name

    def test_active_state_switches_between_preset_and_custom(self, widget):
        """Active styling moves correctly between preset and custom locations."""
        custom_path = Path.home() / "Projects"
        widget.set_custom_location(custom_path)

        widget.set_active_location_by_path(custom_path)
        assert widget._custom_location_button.property("active") == "true"

        widget.set_active_location_by_path(Path.home())
        assert widget._custom_location_button.property("active") == "false"
        assert widget._location_buttons[0].property("active") == "true"


class TestSidebarWidgetStorage:
    """Tests for multi-drive storage indicators in the sidebar."""

    def test_storage_section_shows_all_drives_with_labels(self, app, qtbot):
        """Each drive gets a label, usage bar, and capacity text."""
        drives = [
            DriveUsage(
                label="System (C:)",
                path=Path("C:\\"),
                total=500 * 1024**3,
                used=200 * 1024**3,
                free=300 * 1024**3,
            ),
            DriveUsage(
                label="2TB SATA SSD (D:)",
                path=Path("D:\\"),
                total=2000 * 1024**3,
                used=1000 * 1024**3,
                free=1000 * 1024**3,
            ),
        ]

        with patch(
            "filesearch.ui.sidebar_widget.list_drive_usage", return_value=drives
        ):
            sidebar = SidebarWidget()
            sidebar.show()
            qtbot.addWidget(sidebar)

        labels = sidebar._storage_container.findChildren(QLabel)
        label_texts = [lbl.text() for lbl in labels]

        assert "System (C:)" in label_texts
        assert "2TB SATA SSD (D:)" in label_texts
        assert any("200.0 GB of 500.0 GB used" in t for t in label_texts)
        assert any("1000.0 GB of 2000.0 GB used" in t for t in label_texts)

        bars = sidebar._storage_container.findChildren(QProgressBar)
        assert len(bars) == 2
        assert bars[0].value() == 40
        assert bars[1].value() == 50

    def test_storage_section_handles_empty_drive_list(self, app, qtbot):
        """When no drives are readable, show an unavailable message."""
        with patch("filesearch.ui.sidebar_widget.list_drive_usage", return_value=[]):
            sidebar = SidebarWidget()
            sidebar.show()
            qtbot.addWidget(sidebar)

        labels = sidebar._storage_container.findChildren(QLabel)
        assert any(lbl.text() == "Storage info unavailable" for lbl in labels)
        assert sidebar._storage_container.findChildren(QProgressBar) == []
