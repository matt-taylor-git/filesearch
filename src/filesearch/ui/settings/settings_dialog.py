"""Settings dialog for the file search application.

This module provides the SettingsDialog class that composes tab widgets
into a tabbed settings interface.
"""

from loguru import logger
from PyQt6.QtWidgets import QDialog, QDialogButtonBox, QTabWidget, QVBoxLayout, QWidget

from filesearch.core.application_runtime import DesktopEffects
from filesearch.core.config_manager import ConfigManager
from filesearch.plugins.plugin_manager import PluginManager
from filesearch.ui.settings.highlight_tab import HighlightSettingsTab
from filesearch.ui.settings.plugin_tab import PluginSettingsTab
from filesearch.ui.settings.search_tab import SearchSettingsTab
from filesearch.ui.settings.ui_tab import UISettingsTab


class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences.

    This class implements a tabbed interface for configuring:
    - Search preferences (directories, case sensitivity, file exclusions)
    - UI preferences (window geometry, font size, display options)
    - Highlighting preferences (color, style, enable/disable)
    - Plugin management (enable, disable, configure)

    Attributes:
        config_manager (ConfigManager): Configuration manager instance
        tabs (QTabWidget): Tab widget containing all settings tabs
    """

    def __init__(
        self,
        config_manager: ConfigManager,
        plugin_manager: PluginManager | None = None,
        parent: QWidget | None = None,
        *,
        desktop_effects: DesktopEffects,
    ) -> None:
        """Initialize the settings dialog.

        Args:
            config_manager: Configuration manager instance
            plugin_manager: Plugin manager instance (optional)
            parent: Parent widget (optional)
        """
        super().__init__(parent)
        self.config_manager = config_manager
        self.plugin_manager = plugin_manager
        self.desktop_effects = desktop_effects
        self.setWindowTitle("Settings")
        self.setMinimumSize(600, 400)

        # Store original config for cancel functionality
        self.original_config = config_manager.get_all().copy()

        self.setup_ui()
        self.load_settings()

        logger.debug("SettingsDialog initialized")

    def setup_ui(self) -> None:
        """Setup the user interface."""
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tab instances
        self.search_tab = SearchSettingsTab(
            desktop_effects=self.desktop_effects,
            home_dir=self.config_manager.home_dir,
        )
        self.ui_tab = UISettingsTab()
        self.highlight_tab = HighlightSettingsTab(desktop_effects=self.desktop_effects)

        # Add tabs to widget
        self.tabs.addTab(self.search_tab, "Search")
        self.tabs.addTab(self.ui_tab, "UI")
        self.tabs.addTab(self.highlight_tab, "Highlighting")

        if self.plugin_manager:
            self.plugin_tab = PluginSettingsTab(
                self.plugin_manager, desktop_effects=self.desktop_effects
            )
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
        reset_button = button_box.button(QDialogButtonBox.StandardButton.Reset)
        if reset_button is not None:
            reset_button.clicked.connect(self.reset_to_defaults)

        main_layout.addWidget(button_box)

        logger.debug("SettingsDialog UI setup completed")

    def load_settings(self) -> None:
        """Load current settings from configuration."""
        try:
            self.search_tab.load_settings(self.config_manager)
            self.ui_tab.load_settings(self.config_manager)
            self.highlight_tab.load_settings(self.config_manager)

            if self.plugin_manager:
                self.plugin_tab.load_settings()

            logger.debug("Settings loaded successfully")

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            self.desktop_effects.show_warning(
                self, "Load Error", f"Error loading settings: {e}"
            )

    def save_settings(self) -> None:
        """Save current settings to configuration."""
        try:
            self.search_tab.save_settings(self.config_manager)
            self.ui_tab.save_settings(self.config_manager)
            self.highlight_tab.save_settings(self.config_manager)

            # Save configuration
            self.config_manager.save()

            logger.info("Settings saved successfully")

        except Exception as e:
            logger.error(f"Error saving settings: {e}")
            self.desktop_effects.show_error(
                self, "Save Error", f"Error saving settings: {e}"
            )
            raise

    def accept(self) -> None:
        """Handle OK button click."""
        try:
            self.save_settings()
            super().accept()
        except Exception as e:
            # Don't close dialog if save failed
            logger.debug(f"Settings dialog remains open after save failure: {e}")

    def reject(self) -> None:
        """Handle Cancel button click."""
        # Restore original config
        self.config_manager._config = self.original_config.copy()
        super().reject()

    def reset_to_defaults(self) -> None:
        """Reset all settings to defaults."""
        confirmed = self.desktop_effects.confirm(
            self,
            "Reset to Defaults",
            "Are you sure you want to reset all settings to their default values?",
        )

        if confirmed:
            self.config_manager.reset_to_defaults()
            self.load_settings()
            logger.info("Settings reset to defaults")
