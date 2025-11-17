"""Unit tests for the settings dialog module."""

import json  # noqa: F401
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch  # noqa: F401

import pytest
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import QApplication, QMessageBox

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import ConfigError  # noqa: F401
from filesearch.ui.settings_dialog import SettingsDialog


@pytest.fixture(scope="module")
def qapp():
    """Create QApplication instance for tests."""
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


class TestSettingsDialog:
    """Test cases for SettingsDialog class."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a ConfigManager instance with temporary directory."""
        with patch("platformdirs.user_config_dir", return_value=str(temp_config_dir)):
            manager = ConfigManager(app_name="testapp", app_author="testauthor")
            yield manager

    @pytest.fixture
    def settings_dialog(self, config_manager, qapp):
        """Create a SettingsDialog instance."""
        dialog = SettingsDialog(config_manager)
        yield dialog
        dialog.close()

    def test_init(self, settings_dialog, config_manager):
        """Test dialog initialization."""
        assert settings_dialog.config_manager == config_manager
        assert settings_dialog.windowTitle() == "Settings"
        assert (
            settings_dialog.tabs.count() == 4
        )  # Search, UI, Performance, Highlighting

    def test_search_tab_ui(self, settings_dialog):
        """Test search tab UI components."""
        # Check that all expected widgets exist
        assert settings_dialog.default_dir_input is not None
        assert settings_dialog.default_dir_browse is not None
        assert settings_dialog.case_sensitive_check is not None
        assert settings_dialog.include_hidden_check is not None
        assert settings_dialog.max_results_spin is not None
        assert settings_dialog.exclude_list is not None
        assert settings_dialog.new_ext_input is not None
        assert settings_dialog.add_ext_button is not None
        assert settings_dialog.remove_ext_button is not None

    def test_ui_tab_ui(self, settings_dialog):
        """Test UI tab UI components."""
        # Check that all expected widgets exist
        assert settings_dialog.window_x_spin is not None
        assert settings_dialog.window_y_spin is not None
        assert settings_dialog.window_width_spin is not None
        assert settings_dialog.window_height_spin is not None
        assert settings_dialog.result_font_size_spin is not None
        assert settings_dialog.show_file_icons_check is not None
        assert settings_dialog.auto_expand_results_check is not None

    def test_performance_tab_ui(self, settings_dialog):
        """Test performance tab UI components."""
        # Check that all expected widgets exist
        assert settings_dialog.thread_count_spin is not None
        assert settings_dialog.enable_cache_check is not None
        assert settings_dialog.cache_ttl_spin is not None

    def test_load_settings_search_preferences(self, settings_dialog, config_manager):
        """Test loading search preferences."""
        # Set some test values
        test_dir = "/test/directory"
        config_manager.set("search_preferences.default_search_directory", test_dir)
        config_manager.set("search_preferences.case_sensitive_search", True)
        config_manager.set("search_preferences.include_hidden_files", True)
        config_manager.set("search_preferences.max_search_results", 500)
        config_manager.set(
            "search_preferences.file_extensions_to_exclude", [".tmp", ".log"]
        )

        # Reload settings
        settings_dialog.load_settings()

        # Verify values loaded correctly
        assert settings_dialog.default_dir_input.text() == test_dir
        assert settings_dialog.case_sensitive_check.isChecked() is True
        assert settings_dialog.include_hidden_check.isChecked() is True
        assert settings_dialog.max_results_spin.value() == 500

        # Check extensions list
        extensions = []
        for i in range(settings_dialog.exclude_list.count()):
            extensions.append(settings_dialog.exclude_list.item(i).text())
        assert ".tmp" in extensions
        assert ".log" in extensions

    def test_load_settings_ui_preferences(self, settings_dialog, config_manager):
        """Test loading UI preferences."""
        # Set some test values
        window_geom = {"x": 50, "y": 60, "width": 1024, "height": 768}
        config_manager.set("ui_preferences.window_geometry", window_geom)
        config_manager.set("ui_preferences.result_font_size", 14)
        config_manager.set("ui_preferences.show_file_icons", False)
        config_manager.set("ui_preferences.auto_expand_results", True)

        # Reload settings
        settings_dialog.load_settings()

        # Verify values loaded correctly
        assert settings_dialog.window_x_spin.value() == 50
        assert settings_dialog.window_y_spin.value() == 60
        assert settings_dialog.window_width_spin.value() == 1024
        assert settings_dialog.window_height_spin.value() == 768
        assert settings_dialog.result_font_size_spin.value() == 14
        assert settings_dialog.show_file_icons_check.isChecked() is False
        assert settings_dialog.auto_expand_results_check.isChecked() is True

    def test_load_settings_performance_settings(self, settings_dialog, config_manager):
        """Test loading performance settings."""
        # Set some test values
        config_manager.set("performance_settings.search_thread_count", 8)
        config_manager.set("performance_settings.enable_search_cache", True)
        config_manager.set("performance_settings.cache_ttl_minutes", 60)

        # Reload settings
        settings_dialog.load_settings()

        # Verify values loaded correctly
        assert settings_dialog.thread_count_spin.value() == 8
        assert settings_dialog.enable_cache_check.isChecked() is True
        assert settings_dialog.cache_ttl_spin.value() == 60
        assert settings_dialog.cache_ttl_spin.isEnabled() is True

    def test_save_settings(self, settings_dialog, config_manager, temp_config_dir):
        """Test saving settings."""
        # Set some values in the UI
        settings_dialog.default_dir_input.setText("/new/test/dir")
        settings_dialog.case_sensitive_check.setChecked(True)
        settings_dialog.max_results_spin.setValue(2000)
        settings_dialog.result_font_size_spin.setValue(16)
        settings_dialog.thread_count_spin.setValue(6)

        # Add an extension
        settings_dialog.new_ext_input.setText(".test")
        settings_dialog.add_extension()

        # Save settings
        settings_dialog.save_settings()

        # Verify values saved correctly
        assert (
            config_manager.get("search_preferences.default_search_directory")
            == "/new/test/dir"
        )
        assert config_manager.get("search_preferences.case_sensitive_search") is True
        assert config_manager.get("search_preferences.max_search_results") == 2000
        assert config_manager.get("ui_preferences.result_font_size") == 16
        assert config_manager.get("performance_settings.search_thread_count") == 6

        # Check extension was saved
        extensions = config_manager.get("search_preferences.file_extensions_to_exclude")
        assert ".test" in extensions

    def test_add_extension(self, settings_dialog):
        """Test adding file extension to exclude list."""
        # Clear existing items first to avoid duplicates with defaults
        settings_dialog.exclude_list.clear()

        # Add extension with dot
        settings_dialog.new_ext_input.setText(".txt")
        settings_dialog.add_extension()

        # Check it was added
        items = []
        for i in range(settings_dialog.exclude_list.count()):
            items.append(settings_dialog.exclude_list.item(i).text())
        assert ".txt" in items

        # Add extension without dot
        settings_dialog.new_ext_input.setText("log")
        settings_dialog.add_extension()

        # Check dot was added automatically
        items = []
        for i in range(settings_dialog.exclude_list.count()):
            items.append(settings_dialog.exclude_list.item(i).text())
        assert ".log" in items

        # Clear input - this should be empty after adding extension
        assert settings_dialog.new_ext_input.text() == ""

    def test_add_duplicate_extension(self, settings_dialog):
        """Test adding duplicate extension shows warning."""
        # Clear existing items first to avoid duplicates with defaults
        settings_dialog.exclude_list.clear()

        # Add extension first time
        settings_dialog.new_ext_input.setText(".tmp")
        settings_dialog.add_extension()

        # Try to add duplicate
        with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
            settings_dialog.new_ext_input.setText(".tmp")
            settings_dialog.add_extension()
            mock_warning.assert_called_once()

    def test_remove_extension(self, settings_dialog):
        """Test removing extension from exclude list."""
        # Clear existing items first to avoid duplicates with defaults
        settings_dialog.exclude_list.clear()

        # Add some extensions
        settings_dialog.exclude_list.addItem(".tmp")
        settings_dialog.exclude_list.addItem(".log")
        settings_dialog.exclude_list.addItem(".swp")

        # Select and remove middle item
        settings_dialog.exclude_list.setCurrentRow(1)
        settings_dialog.remove_extension()

        # Check it was removed
        items = []
        for i in range(settings_dialog.exclude_list.count()):
            items.append(settings_dialog.exclude_list.item(i).text())
        assert ".tmp" in items
        assert ".log" not in items
        assert ".swp" in items

    def test_cache_toggle(self, settings_dialog):
        """Test cache enable/disable toggle."""
        # Initially disabled
        assert settings_dialog.cache_ttl_spin.isEnabled() is False

        # Enable cache
        settings_dialog.enable_cache_check.setChecked(True)
        settings_dialog.on_cache_toggled(True)
        assert settings_dialog.cache_ttl_spin.isEnabled() is True

        # Disable cache
        settings_dialog.enable_cache_check.setChecked(False)
        settings_dialog.on_cache_toggled(False)
        assert settings_dialog.cache_ttl_spin.isEnabled() is False

    def test_reset_to_defaults(self, settings_dialog, config_manager):
        """Test reset to defaults functionality."""
        # Set some custom values
        config_manager.set("search_preferences.max_search_results", 9999)
        config_manager.set("ui_preferences.result_font_size", 24)

        # Mock confirmation dialog
        with patch(
            "PyQt6.QtWidgets.QMessageBox.question",
            return_value=QMessageBox.StandardButton.Yes,
        ):
            settings_dialog.reset_to_defaults()

        # Verify values were reset
        assert config_manager.get("search_preferences.max_search_results") == 1000
        assert config_manager.get("ui_preferences.result_font_size") == 12

    def test_reset_to_defaults_cancelled(self, settings_dialog, config_manager):
        """Test reset to defaults when user cancels."""
        # Set some custom values
        config_manager.set("search_preferences.max_search_results", 9999)

        # Mock cancellation
        with patch(
            "PyQt6.QtWidgets.QMessageBox.question",
            return_value=QMessageBox.StandardButton.No,
        ):
            settings_dialog.reset_to_defaults()

        # Verify values were NOT reset
        assert config_manager.get("search_preferences.max_search_results") == 9999

    def test_accept_saves_settings(self, settings_dialog):
        """Test that accept saves settings."""
        # Mock save_settings to verify it's called
        with patch.object(settings_dialog, "save_settings") as mock_save:
            settings_dialog.accept()
            mock_save.assert_called_once()

    def test_reject_restores_config(self, settings_dialog, config_manager):
        """Test that reject restores original config."""
        # Store original config
        original_config = config_manager.get_all().copy()

        # Modify config
        config_manager.set("search_preferences.max_search_results", 7777)

        # Reject dialog
        settings_dialog.reject()

        # Verify config was restored
        assert (
            config_manager.get("search_preferences.max_search_results")
            == original_config["search_preferences"]["max_search_results"]
        )

    def test_load_settings_error_handling(self, settings_dialog, config_manager):
        """Test error handling during settings load."""
        # Mock the config_manager.get to raise an exception
        with patch.object(
            settings_dialog.config_manager, "get", side_effect=Exception("Load error")
        ):
            with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
                settings_dialog.load_settings()
                # Should not crash, error is logged and warning shown
                mock_warning.assert_called_once()

    def test_save_settings_error_handling(self, settings_dialog):
        """Test error handling during settings save."""
        # Mock an error during save
        with patch.object(
            settings_dialog.config_manager, "save", side_effect=Exception("Save error")
        ):
            with patch("PyQt6.QtWidgets.QMessageBox.critical") as mock_critical:
                try:
                    settings_dialog.save_settings()
                except Exception:
                    pass  # Expected to raise
                mock_critical.assert_called_once()


class TestSettingsDialogIntegration:
    """Integration tests for SettingsDialog with ConfigManager."""

    @pytest.fixture
    def temp_config_dir(self):
        """Create a temporary config directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def config_manager(self, temp_config_dir):
        """Create a ConfigManager instance with temporary directory."""
        with patch("platformdirs.user_config_dir", return_value=str(temp_config_dir)):
            manager = ConfigManager(app_name="testapp", app_author="testauthor")
            yield manager

    def test_full_settings_workflow(self, config_manager, temp_config_dir, qapp):
        """Test complete settings workflow: load, modify, save, reload."""
        # Initial values
        config_manager.set("search_preferences.max_search_results", 1000)
        config_manager.set("ui_preferences.result_font_size", 12)
        config_manager.save()

        # Create dialog and modify settings
        dialog = SettingsDialog(config_manager)
        dialog.max_results_spin.setValue(2500)
        dialog.result_font_size_spin.setValue(18)
        dialog.accept()  # This should save

        # Create new config manager (simulating app restart)
        with patch("platformdirs.user_config_dir", return_value=str(temp_config_dir)):
            new_manager = ConfigManager(app_name="testapp", app_author="testauthor")

            # Verify settings persisted
            assert new_manager.get("search_preferences.max_search_results") == 2500
            assert new_manager.get("ui_preferences.result_font_size") == 18

        dialog.close()

    def test_cancel_does_not_save(self, config_manager, temp_config_dir, qapp):
        """Test that cancel does not save changes."""
        # Initial values
        config_manager.set("search_preferences.max_search_results", 1000)
        config_manager.save()

        # Create dialog and modify settings
        dialog = SettingsDialog(config_manager)
        dialog.max_results_spin.setValue(3000)
        dialog.reject()  # This should NOT save

        # Create new config manager (simulating app restart)
        with patch("platformdirs.user_config_dir", return_value=str(temp_config_dir)):
            new_manager = ConfigManager(app_name="testapp", app_author="testauthor")

            # Verify settings were NOT changed
            assert new_manager.get("search_preferences.max_search_results") == 1000

        dialog.close()
