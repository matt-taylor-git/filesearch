"""Settings dialog for the file search application.

This module provides the SettingsDialog class that composes tab widgets
into a tabbed settings interface.
"""

from typing import Optional

from loguru import logger
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QMessageBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.plugins.plugin_manager import PluginManager
from filesearch.ui.settings.highlight_tab import HighlightSettingsTab
from filesearch.ui.settings.performance_tab import PerformanceSettingsTab
from filesearch.ui.settings.plugin_tab import PluginSettingsTab
from filesearch.ui.settings.search_tab import SearchSettingsTab
from filesearch.ui.settings.ui_tab import UISettingsTab


class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences.

    This class implements a tabbed interface for configuring:
    - Search preferences (directories, case sensitivity, file exclusions)
    - UI preferences (window geometry, font size, display options)
    - Performance settings (thread count, caching)
    - Highlighting preferences (color, style, enable/disable)
    - Plugin management (enable, disable, configure)

    Attributes:
        config_manager (ConfigManager): Configuration manager instance
        tabs (QTabWidget): Tab widget containing all settings tabs
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        plugin_manager: Optional[PluginManager] = None,
        parent: Optional[QWidget] = None,
    ):
        """Initialize the settings dialog.

        Args:
            config_manager: Configuration manager instance
            plugin_manager: Plugin manager instance (optional)
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)

        # Store original config for cancel functionality
        self.original_config = config_manager.get_all().copy()

        self.setup_ui()
        self.load_settings()

        logger.debug("SettingsDialog initialized")

    def __getattr__(self, name: str):
        """Delegate attribute lookups to tab widgets for backward compatibility.

        This allows code like ``dialog.default_dir_input`` to resolve to
        ``dialog.search_tab.default_dir_input`` transparently.
        """
        # Avoid infinite recursion during init (before tabs are created)
        tabs = ("search_tab", "ui_tab", "performance_tab", "highlight_tab", "plugin_tab")
        for tab_name in tabs:
            try:
                tab = object.__getattribute__(self, tab_name)
            except AttributeError:
                continue
            try:
                return getattr(tab, name)
            except AttributeError:
                continue
        raise AttributeError(
            f"'{type(self).__name__}' object has no attribute '{name}'"
        )

    def setup_ui(self) -> None:
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tab instances
        self.search_tab = SearchSettingsTab()
        self.ui_tab = UISettingsTab()
        self.performance_tab = PerformanceSettingsTab()
        self.highlight_tab = HighlightSettingsTab()

        # Add tabs to widget
        self.tabs.addTab(self.search_tab, "Search")
        self.tabs.addTab(self.ui_tab, "UI")
        self.tabs.addTab(self.performance_tab, "Performance")
        self.tabs.addTab(self.highlight_tab, "Highlighting")

        if self.plugin_manager:
            self.plugin_tab = PluginSettingsTab(self.plugin_manager)
            self.tabs.addTab(self.plugin_tab, "Plugins")

        # Create button box
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
            | QDialogButtonBox.StandardButton.Reset
        )

        # Connect button signals
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        button_box.button(QDialogButtonBox.StandardButton.Reset).clicked.connect(
            self.reset_to_defaults
        )

        main_layout.addWidget(button_box)

        logger.debug("SettingsDialog UI setup completed")

    def load_settings(self) -> None:
        """Load current settings from configuration."""
        try:
            self.search_tab.load_settings(self.config_manager)
            self.ui_tab.load_settings(self.config_manager)
            self.performance_tab.load_settings(self.config_manager)
            self.highlight_tab.load_settings(self.config_manager)

            if self.plugin_manager:
                self.plugin_tab.load_settings()

            logger.debug("Settings loaded successfully")

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Load Error", f"Error loading settings: {e}")

    def save_settings(self) -> None:
        """Save current settings to configuration."""
        try:
            self.search_tab.save_settings(self.config_manager)
            self.ui_tab.save_settings(self.config_manager)
            self.performance_tab.save_settings(self.config_manager)
            self.highlight_tab.save_settings(self.config_manager)

            # Save configuration
            self.config_manager.save()

            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            QMessageBox.critical(self, "Save Error", f"Error saving settings: {e}")
            raise

    def accept(self) -> None:
        """Handle OK button click."""
        try:
            self.save_settings()
            super().accept()
        except Exception:
            # Don't close dialog if save failed
            pass

    def reject(self) -> None:
        """Handle Cancel button click."""
        # Restore original config
        self.config_manager._config = self.original_config.copy()
        super().reject()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        reply = QMessageBox.question(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            self.config_manager.reset_to_defaults()
            self.load_settings()
            logger.info("Settings reset to defaults")
