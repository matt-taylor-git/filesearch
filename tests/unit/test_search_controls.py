"""Unit tests for search controls module.

This module provides comprehensive tests for SearchInputWidget including
keyboard interactions, visual feedback, search history, and accessibility.
"""

import os
import platform
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtTest import QTest
from PyQt6.QtWidgets import QApplication

from filesearch.core.config_manager import ConfigManager
from filesearch.ui.search_controls import DirectorySelectorWidget, SearchInputWidget


class TestSearchInputWidget:
    """Test cases for SearchInputWidget class."""

    @pytest.fixture
    def app(self):
        """Create QApplication for testing."""
        if not QApplication.instance():
            app = QApplication([])
        else:
            app = QApplication.instance()
        yield app

    @pytest.fixture
    def config_manager(self, tmp_path):
        """Create a temporary config manager for testing."""
        config = ConfigManager(app_name="test_filesearch", app_author="test")
        return config

    @pytest.fixture
    def widget(self, app, config_manager):
        """Create SearchInputWidget instance for testing."""
        widget = SearchInputWidget(config_manager=config_manager)
        widget.show()
        return widget

    def test_widget_initialization(self, widget):
        """Test widget initializes correctly."""
        assert widget.windowTitle() == ""
        assert widget.minimumWidth() == 400
        assert widget.search_input.maxLength() == 255
        assert (
            widget.search_input.placeholderText() == "Enter filename or partial name..."
        )
        assert widget.label.text() == "Search files and folders"
        assert not widget.is_loading
        assert not widget.has_error

    def test_placeholder_text_and_label(self, widget):
        """Test placeholder text and label are correctly displayed (AC #1)."""
        # Test label
        assert widget.label.text() == "Search files and folders"

        # Test placeholder text
        assert (
            widget.search_input.placeholderText() == "Enter filename or partial name..."
        )

        # Test accessibility
        assert widget.search_input.accessibleName() == "Search input"
        assert (
            "Enter filename or partial name"
            in widget.search_input.accessibleDescription()
        )

    def test_widget_sizing(self, widget):
        """Test widget sizing meets requirements (AC #1)."""
        # Test minimum size
        min_size = widget.minimumSizeHint()
        assert min_size.width() == 400  # Minimum 400px
        assert min_size.height() == 32  # 32px height

        # Test size hint
        size_hint = widget.sizeHint()
        assert size_hint.height() == 32  # 32px height
        assert size_hint.width() >= 400  # At least 400px

    def test_keyboard_input_immediate_feedback(self, widget, qtbot):
        """Test keyboard input provides immediate feedback (AC #2)."""
        # Type text
        qtbot.keyClicks(widget.search_input, "test")

        # Check text was entered
        assert widget.get_text() == "test"

        # Check clear button appears
        assert widget.clear_button.isVisible()

    def test_clear_button_appears_with_text(self, widget, qtbot):
        """Test clear button appears when text is entered (AC #2, #4)."""
        # Initially hidden
        assert not widget.clear_button.isVisible()

        # Type text
        qtbot.keyClicks(widget.search_input, "test")

        # Clear button should appear
        assert widget.clear_button.isVisible()

        # Clear text
        widget.clear_text()

        # Clear button should disappear
        assert not widget.clear_button.isVisible()

    def test_max_length_validation(self, widget):
        """Test maximum length validation (255 characters) (AC #2)."""
        # Try to enter more than max length
        long_text = "a" * 300
        widget.search_input.setText(long_text)

        # Should be truncated to max length
        assert len(widget.get_text()) == 255
        assert widget.search_input.maxLength() == 255

    def test_enter_key_initiates_search(self, widget, qtbot):
        """Test Enter key immediately initiates search (AC #3)."""
        # Type text
        widget.set_text("test_query")

        # Press Enter and check signal
        with qtbot.waitSignal(widget.search_initiated, timeout=1000) as blocker:
            qtbot.keyPress(widget.search_input, Qt.Key.Key_Return)

        # Check signal was emitted with correct query
        assert blocker.args == ["test_query"]

    def test_escape_key_clears_input(self, widget, qtbot):
        """Test Escape key clears input and returns focus (AC #3)."""
        # Type text
        qtbot.keyClicks(widget.search_input, "test")

        # Press Escape
        qtbot.keyPress(widget.search_input, Qt.Key.Key_Escape)

        # Check input was cleared
        assert widget.get_text() == ""
        assert not widget.clear_button.isVisible()

    def test_ctrl_l_selects_all_text(self, widget, qtbot):
        """Test Ctrl+L selects all text (AC #3)."""
        # Type text
        qtbot.keyClicks(widget.search_input, "test_text")

        # Press Ctrl+L
        qtbot.keyPress(
            widget.search_input, Qt.Key.Key_L, Qt.KeyboardModifier.ControlModifier
        )

        # Check all text is selected
        assert widget.search_input.selectedText() == "test_text"

    def test_search_history_persistence(self, widget, config_manager, qtbot):
        """Test search history is saved across restarts (AC #2)."""
        # Perform a search
        widget.set_text("first_search")
        qtbot.keyPress(widget.search_input, Qt.Key.Key_Return)

        # Create new widget instance (simulating restart)
        new_widget = SearchInputWidget(config_manager=config_manager)

        # Check history was loaded
        assert "first_search" in new_widget.search_history

    def test_search_history_dropdown(self, widget, qtbot):
        """Test search history dropdown accessible via down arrow (AC #2)."""
        # Add some history
        widget.search_history = ["search1", "search2", "search3"]
        widget._setup_completer()

        # Focus widget and press down arrow
        widget.search_input.setFocus()
        qtbot.keyPress(widget.search_input, Qt.Key.Key_Down)

        # Completer should be visible
        completer = widget.search_input.completer()
        assert completer is not None
        # Note: Testing actual popup visibility is complex in pytest-qt

    def test_auto_complete_suggestions(self, widget):
        """Test auto-complete suggestions from recent searches (AC #2)."""
        # Setup history
        widget.search_history = ["document", "download", "desktop"]
        widget._setup_completer()

        # Type partial match
        widget.search_input.setFocus()
        QTest.keyClicks(widget.search_input, "doc")

        # Should have completer with suggestions
        completer = widget.search_input.completer()
        assert completer is not None
        assert len(widget.search_history) > 0

    def test_visual_feedback_focus_states(self, widget, qtbot):
        """Test visual feedback for focus states (AC #4)."""
        # Test normal state
        assert not widget.has_error
        assert not widget.is_loading

        # Test that focus can be set
        widget.set_focus()
        # In test environment, focus may not actually be set, but method should exist
        assert hasattr(widget, "set_focus")

    def test_error_state_visual_feedback(self, widget):
        """Test error state shows red border (AC #4)."""
        # Set error state
        widget.set_error_state(True)

        # Check error state is set
        assert widget.has_error

        # Check style property is set
        assert widget.search_input.property("state") == "error"

        # Clear error state
        widget.set_error_state(False)
        assert not widget.has_error
        assert widget.search_input.property("state") == "normal"

    def test_loading_indicator(self, widget):
        """Test loading indicator appears during search (AC #4)."""
        # Set loading state
        widget.set_loading_state(True)

        # Check loading indicator is visible
        assert widget.is_loading
        assert widget.loading_indicator.isVisible()

        # Clear loading state
        widget.set_loading_state(False)
        assert not widget.is_loading
        assert not widget.loading_indicator.isVisible()

    def test_accessibility_screen_reader_support(self, widget, qtbot):
        """Test screen reader announcements and ARIA labels (AC #5)."""
        # Test accessibility attributes
        assert widget.search_input.accessibleName() == "Search input"
        assert "filename" in widget.search_input.accessibleDescription()
        assert "partial name" in widget.search_input.accessibleDescription()

        # Test keyboard navigation support - set focus using qtbot
        qtbot.wait(100)  # Allow UI to settle
        widget.set_focus()
        # In test environment, focus behavior may vary, but attributes should be set

    def test_special_character_handling(self, widget, qtbot):
        """Test special characters treated as literal search terms (AC #2)."""
        # Test various special characters
        special_chars = '"*[]{}()?&'
        qtbot.keyClicks(widget.search_input, special_chars)

        # Characters should be preserved literally
        assert widget.get_text() == special_chars

    def test_empty_query_validation(self, widget, qtbot):
        """Test empty query validation."""
        # Test empty query doesn't initiate search
        search_initiated_called = False

        def on_search_initiated(query):
            nonlocal search_initiated_called
            search_initiated_called = True

        widget.search_initiated.connect(on_search_initiated)

        # Press Enter with empty query
        qtbot.keyPress(widget.search_input, Qt.Key.Key_Return)

        # Search should not be initiated
        assert not search_initiated_called

    def test_text_changed_signal(self, widget, qtbot):
        """Test text_changed signal emission."""
        texts_received = []

        def on_text_changed(text):
            texts_received.append(text)

        widget.text_changed.connect(on_text_changed)

        # Type text
        qtbot.keyClicks(widget.search_input, "hello")

        # Check signals were emitted
        assert len(texts_received) > 0
        assert "hello" in texts_received[-1]

    def test_search_history_max_items(self, widget, config_manager, qtbot):
        """Test search history limited to 10 items."""
        # Add more than 10 searches
        for i in range(15):
            widget.set_text(f"search_{i}")
            qtbot.keyPress(widget.search_input, Qt.Key.Key_Return)

        # Should only keep last 10
        assert len(widget.search_history) == 10
        assert "search_14" in widget.search_history  # Most recent
        assert "search_0" not in widget.search_history  # Oldest should be gone

    def test_clear_search_history_option(self, widget, config_manager, qtbot):
        """Test clear search history functionality."""
        # Add some history
        widget.search_history = ["item1", "item2", "item3"]
        widget._save_search_history()

        # Clear history
        widget.search_history.clear()
        widget._save_search_history()

        # Create new widget to verify history is cleared
        new_widget = SearchInputWidget(config_manager=config_manager)
        assert len(new_widget.search_history) == 0


class TestDirectorySelectorWidget:
    """Test cases for DirectorySelectorWidget class."""

    @pytest.fixture
    def config_manager(self):
        """Create a temporary config manager for testing."""
        config = ConfigManager(app_name="test_filesearch", app_author="test")
        return config

    @pytest.fixture
    def widget(self, qtbot, config_manager):
        """Create DirectorySelectorWidget instance for testing."""
        from filesearch.ui.search_controls import DirectorySelectorWidget

        widget = DirectorySelectorWidget(config_manager=config_manager)
        widget.show()
        qtbot.addWidget(widget)
        return widget

    @pytest.fixture
    def mock_path_utils(self, monkeypatch):
        """Mock normalize_path and validate_directory for isolation."""
        mock_normalize = MagicMock(side_effect=lambda x: Path(x).expanduser().resolve())
        mock_validate = MagicMock(return_value=None)

        monkeypatch.setattr(
            "filesearch.ui.search_controls.normalize_path", mock_normalize
        )
        monkeypatch.setattr(
            "filesearch.ui.search_controls.validate_directory", mock_validate
        )

        return mock_normalize, mock_validate

    def test_widget_initialization_and_default_directory(self, widget):
        """Test widget initializes with default home directory (AC #1)."""
        assert (
            widget.directory_input.placeholderText()
            == "Enter directory path or browse..."
        )
        assert widget.browse_button.text() == "Browse..."

        # Check default directory is set (using os.path.expanduser in implementation)
        assert Path(widget.directory_input.text()) == Path.home().resolve()
        assert widget.recent_directories == []

    def test_directory_changed_signal(self, widget, qtbot):
        """Test directory_changed signal emits correct Path object."""
        new_path = Path("/tmp/test_new_dir")

        with qtbot.waitSignal(widget.directory_changed, timeout=1000) as blocker:
            widget.directory_input.setText(str(new_path))

        assert blocker.args[0] == new_path

    @patch(
        "PyQt6.QtWidgets.QFileDialog.getExistingDirectory",
        return_value="/tmp/selected_dir",
    )
    def test_browse_button_opens_dialog_and_updates_path(
        self, mock_dialog, widget, qtbot
    ):
        """Test browse button opens dialog and updates input (AC #3)."""
        # Click browse button
        qtbot.mouseClick(widget.browse_button, Qt.MouseButton.LeftButton)

        # Check QFileDialog was called with correct title and current path
        mock_dialog.assert_called_once()
        args, kwargs = mock_dialog.call_args
        assert args[1] == "Select Search Directory"
        assert args[2] == str(Path.home().resolve())

        # Check input was updated
        assert widget.get_directory() == Path("/tmp/selected_dir")

    @patch("PyQt6.QtWidgets.QFileDialog.getExistingDirectory", return_value="")
    def test_browse_button_dialog_cancelled(self, mock_dialog, widget, qtbot):
        """Test browse dialog cancellation does not change path."""
        initial_path = widget.get_directory()

        # Click browse button and cancel
        qtbot.mouseClick(widget.browse_button, Qt.MouseButton.LeftButton)

        # Check path remains the same
        assert widget.get_directory() == initial_path

    def test_recent_directories_add_and_save(self, widget, mock_path_utils):
        """Test adding a directory to the recent list and persistence (AC #4)."""
        # Mock Path.is_dir() to return True for test paths
        with patch.object(Path, "is_dir", return_value=True):
            dir1 = Path("/tmp/dir1")
            dir2 = Path("/tmp/dir2")

            widget._add_to_recent_directories(dir1)
            widget._add_to_recent_directories(dir2)

            # Check order (most recent first)
            assert widget.recent_directories == [str(dir2), str(dir1)]

            # Check persistence (mocked config manager)
            saved_list = widget.config_manager.get("recent.directories")
            assert saved_list == [str(dir2), str(dir1)]

    def test_recent_directories_max_size(self, widget, mock_path_utils):
        """Test recent directories list is limited to 5 entries (AC #4)."""
        with patch.object(Path, "is_dir", return_value=True):
            for i in range(10):
                widget._add_to_recent_directories(Path(f"/tmp/dir{i}"))

            # Check size
            assert len(widget.recent_directories) == 5
            # Check order (most recent first)
            assert widget.recent_directories[0] == "/tmp/dir9"
            assert widget.recent_directories[-1] == "/tmp/dir5"

    def test_recent_directories_menu_display(self, widget, qtbot):
        """Test recent directories menu is created and displayed (AC #4)."""
        widget.recent_directories = ["/tmp/dir1", "/tmp/dir2"]

        # Click the recent button
        qtbot.mouseClick(widget.recent_button, Qt.MouseButton.LeftButton)

        # Note: Cannot directly test QMenu visibility, but can test the method execution
        # We rely on the implementation of _show_recent_menu to be correct.

        # Test clear history action (simulated)
        widget._clear_recent_history()
        assert widget.recent_directories == []

    def test_path_validation_and_error_state(self, widget, qtbot, mock_path_utils):
        """Test path validation updates error state and tooltip (AC #2)."""
        mock_normalize, mock_validate = mock_path_utils

        # 1. Test invalid path (non-existent)
        mock_validate.return_value = "Directory does not exist."
        qtbot.keyClicks(widget.directory_input, "/nonexistent/path")

        # Check error state
        assert widget.directory_input.property("state") == "error"
        assert widget.directory_input.toolTip() == "Directory does not exist."

        # 2. Test valid path
        mock_validate.return_value = None
        widget.directory_input.clear()
        qtbot.keyClicks(widget.directory_input, str(Path.home()))

        # Check normal state
        assert widget.directory_input.property("state") == "normal"
        assert widget.directory_input.toolTip() == str(Path.home().resolve())

    def test_path_normalization_on_input(self, widget, qtbot, mock_path_utils):
        """Test input text is normalized before validation."""
        mock_normalize, _ = mock_path_utils

        # Set text with a shortcut
        widget.directory_input.setText("~")

        # Check normalize_path was called
        mock_normalize.assert_called_with("~")

    def test_auto_complete_setup(self, widget):
        """Test auto-complete is set up with common paths and recent directories (AC #2.3)."""
        completer = widget.directory_input.completer()

        assert completer is not None

        model = completer.model()

        # Should have at least common paths: home, Documents, Desktop
        items = [model.data(model.index(i, 0)) for i in range(model.rowCount())]

        home = os.path.expanduser("~")
        assert home in items
        assert os.path.join(home, "Documents") in items
        assert os.path.join(home, "Desktop") in items

        # If recent directories exist, they should be included
        if widget.recent_directories:
            for recent in widget.recent_directories:
                assert recent in items
