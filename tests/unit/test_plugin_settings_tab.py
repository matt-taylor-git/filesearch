"""User-visible behavior tests for plugin settings workflows."""

from types import SimpleNamespace
from unittest.mock import Mock

from PyQt6.QtCore import Qt

from filesearch.ui.settings.plugin_tab import PluginSettingsTab


def plugin_status():
    return {
        "enabled": {
            "name": "Enabled plugin",
            "version": "1.0",
            "loaded": True,
            "enabled": True,
        },
        "disabled": {
            "name": "Disabled plugin",
            "version": "2.0",
            "loaded": True,
            "enabled": False,
        },
        "missing": {
            "name": "Missing plugin",
            "version": "3.0",
            "loaded": False,
            "enabled": False,
        },
    }


def make_tab(qtbot, desktop_effects):
    manager = Mock()
    manager.get_plugin_status.return_value = plugin_status()
    tab = PluginSettingsTab(manager, desktop_effects=desktop_effects)
    qtbot.addWidget(tab)
    tab.load_settings()
    return tab, manager


def select_plugin(tab, plugin_name: str) -> None:
    for row in range(tab.plugin_list.count()):
        item = tab.plugin_list.item(row)
        if item.data(Qt.ItemDataRole.UserRole) == plugin_name:
            tab.plugin_list.setCurrentItem(item)
            return
    raise AssertionError(f"Plugin {plugin_name} was not shown")


def test_plugin_tab_renders_loaded_enabled_and_missing_states(qtbot, desktop_effects):
    tab, _manager = make_tab(qtbot, desktop_effects)

    assert tab.plugin_list.count() == 3
    texts = [tab.plugin_list.item(row).text() for row in range(3)]
    assert any("[Loaded] [Enabled]" in text for text in texts)
    assert any("[Loaded] [Disabled]" in text for text in texts)
    assert any("[Not Loaded]" in text for text in texts)
    assert tab.plugin_status_label.text() == "Loaded: 2, Enabled: 1"


def test_plugin_tab_enable_and_disable_refresh_after_success(qtbot, desktop_effects):
    tab, manager = make_tab(qtbot, desktop_effects)
    manager.enable_plugin.return_value = True
    manager.disable_plugin.return_value = True

    select_plugin(tab, "disabled")
    tab.enable_plugin_button.click()
    manager.enable_plugin.assert_called_once_with("disabled")

    select_plugin(tab, "enabled")
    tab.disable_plugin_button.click()
    manager.disable_plugin.assert_called_once_with("enabled")
    assert manager.get_plugin_status.call_count == 3


def test_plugin_tab_reports_enable_and_disable_failures(qtbot, desktop_effects):
    tab, manager = make_tab(qtbot, desktop_effects)
    manager.enable_plugin.return_value = False
    manager.disable_plugin.return_value = False

    select_plugin(tab, "disabled")
    tab.enable_selected_plugin()
    select_plugin(tab, "enabled")
    tab.disable_selected_plugin()

    assert desktop_effects.warnings == [
        ("Enable Failed", "Failed to enable plugin: disabled"),
        ("Disable Failed", "Failed to disable plugin: enabled"),
    ]


def test_plugin_tab_shows_plugin_configuration(qtbot, desktop_effects):
    tab, manager = make_tab(qtbot, desktop_effects)
    manager.get_plugin.return_value = SimpleNamespace(config={"limit": 5})
    select_plugin(tab, "enabled")

    tab.configure_selected_plugin()

    assert desktop_effects.information == [("Plugin Config: enabled", "limit: 5")]

    manager.get_plugin.return_value = SimpleNamespace(config={})
    tab.configure_selected_plugin()
    assert desktop_effects.information[-1] == (
        "Plugin Config: enabled",
        "No configuration",
    )


def test_plugin_tab_warns_when_selected_plugin_is_not_loaded(qtbot, desktop_effects):
    tab, manager = make_tab(qtbot, desktop_effects)
    manager.get_plugin.return_value = None
    select_plugin(tab, "missing")

    tab.configure_plugin_button.click()

    assert desktop_effects.warnings == [
        ("Plugin Not Loaded", "Plugin missing is not loaded")
    ]


def test_plugin_tab_actions_are_noops_without_a_selection(qtbot, desktop_effects):
    tab, manager = make_tab(qtbot, desktop_effects)
    tab.plugin_list.clearSelection()
    tab.plugin_list.setCurrentItem(None)

    tab.enable_selected_plugin()
    tab.disable_selected_plugin()
    tab.configure_selected_plugin()

    manager.enable_plugin.assert_not_called()
    manager.disable_plugin.assert_not_called()
    manager.get_plugin.assert_not_called()
