import os
import sys
from pathlib import Path

import pytest
from PyQt6.QtCore import QItemSelectionModel, QPoint, Qt
from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMenu

from filesearch.models.search_result import SearchResult
from filesearch.ui.main_window import MainWindow


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
        ),
    ]
    # Ensure results view is populated
    main_window.results_view.set_results(results)
    # Select the first item for context menu interaction
    main_window.results_view.setCurrentIndex(
        main_window.results_view.model().index(0, 0)
    )
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


def test_context_menu_creation_and_actions(main_window, add_search_results):
    """
    Test that the context menu infrastructure creates a menu with the expected actions.
    This tests the core menu creation logic without requiring mouse events.
    """
    # Get selected results - simulate having one item selected
    selected_results = [add_search_results[0]]  # Use first result

    # Test that the context menu creation method works
    context_menu = main_window._create_context_menu(selected_results)

    assert context_menu is not None, "Context menu creation failed."
    assert isinstance(context_menu, QMenu), "Context menu should be a QMenu instance."

    # AC1: Basic Context Menu Display - Check all expected options
    expected_actions = [
        "Open",
        "Open With...",
        "Open Containing Folder",
        "Copy Path to Clipboard",
        "Copy File to Clipboard",
        "Properties",
        "Delete",
        "Rename",
    ]

    actual_actions = get_visible_menu_actions(context_menu)
    assert (
        actual_actions == expected_actions
    ), f"Actions mismatch.\nGot: {actual_actions}\nExpected: {expected_actions}"

    # AC1: Open (default action, bold text)
    open_action = get_action_by_text(context_menu, "Open")
    assert open_action is not None, "Open action not found."
    assert open_action.font().bold(), "Open action should be bold."

    # AC2: Menu Keyboard Shortcuts
    open_folder_action = get_action_by_text(context_menu, "Open Containing Folder")
    assert open_folder_action is not None, "Open Containing Folder action not found."
    assert (
        open_folder_action.shortcut().toString() == "Ctrl+Shift+O"
    ), "Open Containing Folder shortcut should be Ctrl+Shift+O"

    copy_path_action = get_action_by_text(context_menu, "Copy Path to Clipboard")
    assert copy_path_action is not None, "Copy Path to Clipboard action not found."
    assert (
        copy_path_action.shortcut().toString() == "Ctrl+Shift+C"
    ), "Copy Path to Clipboard shortcut should be Ctrl+Shift+C"

    properties_action = get_action_by_text(context_menu, "Properties")
    assert properties_action is not None, "Properties action not found."
    assert (
        properties_action.shortcut().toString() == "Alt+Return"
    ), "Properties shortcut should be Alt+Return"

    delete_action = get_action_by_text(context_menu, "Delete")
    assert delete_action is not None, "Delete action not found."
    assert delete_action.shortcut().toString() == "Del", "Delete shortcut should be Del"

    rename_action = get_action_by_text(context_menu, "Rename")
    assert rename_action is not None, "Rename action not found."
    assert rename_action.shortcut().toString() == "F2", "Rename shortcut should be F2"

    # AC11: Multi-Selection Support - Test with single selection
    # (Open With..., Properties, Rename should be enabled)
    open_with_menu = None
    for action in context_menu.actions():
        if action.text() == "Open With...":
            open_with_menu = action.menu()
            break

    assert open_with_menu is not None, "Open With... submenu not found."
    # In single selection, Open With... should be enabled
    # Note: We can't easily test disabled state without recreating the menu


def test_context_menu_multi_selection(main_window, add_search_results):
    """
    Test context menu behavior with multiple selections.
    """
    # Test with multiple results selected
    selected_results = add_search_results  # Use both results

    context_menu = main_window._create_context_menu(selected_results)

    # AC11: With multiple selection, Open With..., Properties, and Rename
    # should be disabled
    open_with_action = None
    properties_action = get_action_by_text(context_menu, "Properties")
    rename_action = get_action_by_text(context_menu, "Rename")

    for action in context_menu.actions():
        if action.text() == "Open With...":
            open_with_action = action
            break

    assert open_with_action is not None, "Open With... action not found."
    assert (
        not open_with_action.isEnabled()
    ), "Open With... should be disabled for multi-selection"

    assert (
        not properties_action.isEnabled()
    ), "Properties should be disabled for multi-selection"
    assert (
        not rename_action.isEnabled()
    ), "Rename should be disabled for multi-selection"

    # Multi-selection actions should remain enabled
    open_action = get_action_by_text(context_menu, "Open")
    copy_path_action = get_action_by_text(context_menu, "Copy Path to Clipboard")
    copy_file_action = get_action_by_text(context_menu, "Copy File to Clipboard")
    delete_action = get_action_by_text(context_menu, "Delete")

    assert open_action.isEnabled(), "Open should be enabled for multi-selection"
    assert (
        copy_path_action.isEnabled()
    ), "Copy Path to Clipboard should be enabled for multi-selection"
    assert (
        copy_file_action.isEnabled()
    ), "Copy File to Clipboard should be enabled for multi-selection"
    assert delete_action.isEnabled(), "Delete should be enabled for multi-selection"
