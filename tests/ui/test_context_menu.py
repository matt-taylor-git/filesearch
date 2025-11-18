import pytest
from PyQt6.QtWidgets import QApplication, QMenu
from PyQt6.QtGui import QAction
from PyQt6.QtCore import Qt, QPoint
from pytestqt.exceptions import QtTestError
from src.filesearch.ui.main_window import MainWindow
from src.filesearch.models.search_result import SearchResult
from pathlib import Path
import os
import sys

# Create a temporary directory and files for testing
@pytest.fixture(scope="session", autouse=True)
def create_test_files(tmp_path_factory):
    test_dir = tmp_path_factory.mktemp("test_dir_context_menu")
    (test_dir / "file1.txt").write_text("content1")
    (test_dir / "subdir").mkdir()
    (test_dir / "subdir" / "file2.py").write_text("print('hello')")
    return test_dir

@pytest.fixture
def main_window(qtbot):
    """Fixture to create and show MainWindow."""
    window = MainWindow()
    window.show()
    qtbot.addWidget(window)
    return window

@pytest.fixture
def add_search_results(main_window, create_test_files):
    """Adds dummy search results to the main window's results view."""
    results = [
        SearchResult(
            path=create_test_files / "file1.txt",
            size=100,
            modified=1678886400,
        ),
        SearchResult(
            path=create_test_files / "subdir" / "file2.py",
            size=200,
            modified=1678972800,
        )
    ]
    # Ensure results view is populated
    main_window.results_view.set_results(results)
    # Select the first item for context menu interaction
    main_window.results_view.setCurrentIndex(main_window.results_view.model().index(0, 0))
    return results

def get_visible_menu_actions(menu: QMenu):
    """Helper to get text of visible actions in a menu."""
    actions = []
    for action in menu.actions():
        if action.isVisible() and action.text():
            actions.append(action.text())
    return actions

def get_action_by_text(menu: QMenu, text: str) -> QAction | None:
    """Helper to get an action by its text."""
    for action in menu.actions():
        if action.text() == text:
            return action
    return None

def test_context_menu_display_and_actions(qtbot, main_window, add_search_results):
    """
    Test that a right-click on a search result displays a context menu
    with the expected actions and properties.
    """
    results_view = main_window.results_view
    qtbot.waitUntil(lambda: results_view.model().rowCount() > 0, timeout=1000)

    # Get the rectangle of the first item to click within it
    index = results_view.model().index(0, 0)
    rect = results_view.visualRect(index)
    
    # Calculate a point within the item to simulate a right-click
    # Ensure it's within the visible part of the item, not just the model's area
    click_pos_local = rect.center()
    
    # Perform a right-click using qtbot
    # The customContextMenuRequested signal will be emitted with this local position
    # main_window's _on_context_menu_requested will then map it to global
    qtbot.mouseClick(results_view.viewport(), Qt.MouseButton.RightButton, pos=click_pos_local)

    # Find the context menu - it should be a top-level widget
    context_menu = None
    for widget in QApplication.topLevelWidgets():
        if isinstance(widget, QMenu) and widget.isVisible():
            context_menu = widget
            break
    
    assert context_menu is not None, "Context menu did not appear."
    assert context_menu.isVisible(), "Context menu is not visible."

    # AC1: Basic Context Menu Display - Check all expected options
    expected_actions = [
        "Open",
        "Open With...",
        "Open Containing Folder",
        "Copy Path to Clipboard",
        "Copy File to Clipboard",
        "Properties",
        "Delete",
        "Rename"
    ]
    
    actual_actions = get_visible_menu_actions(context_menu)
    assert actual_actions == expected_actions, \
        f"Context menu actions do not match expectations. Got: {actual_actions}, Expected: {expected_actions}"

    # AC1: Open (default action, bold text)
    open_action = get_action_by_text(context_menu, "Open")
    assert open_action is not None, "Open action not found."
    assert open_action.font().bold(), "Open action should be bold."

    # AC2: Menu Position and Appearance
    # Verify menu appears at mouse cursor position (approximately)
    # The actual position might be slightly offset by the OS/Qt styling.
    # We map the results_view local click position to global, then compare to menu's global position.
    click_pos_global = results_view.mapToGlobal(click_pos_local)
    menu_global_pos = context_menu.pos()

    # Allow some pixel tolerance
    tolerance = 20 
    assert abs(menu_global_pos.x() - click_pos_global.x()) < tolerance, \
        f"Menu X position {menu_global_pos.x()} not close to click X position {click_pos_global.x()}"
    assert abs(menu_global_pos.y() - click_pos_global.y()) < tolerance, \
        f"Menu Y position {menu_global_pos.y()} not close to click Y position {click_pos_global.y()}"
    
    # Test that clicking outside closes the menu (implicit with qtbot context)
    # Simulate an escape key press to close the menu
    qtbot.keyPress(context_menu, Qt.Key.Key_Escape)
    qtbot.wait(100) # Give it a moment to close
    assert not context_menu.isVisible(), "Context menu did not close on Escape."
