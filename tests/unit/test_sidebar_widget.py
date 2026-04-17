"""Unit tests for the sidebar widget."""

from pathlib import Path

import pytest
from PyQt6.QtWidgets import QApplication

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
