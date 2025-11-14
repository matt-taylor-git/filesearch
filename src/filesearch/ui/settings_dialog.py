"""Settings dialog module for the file search application.

This module provides the SettingsDialog class that implements a tabbed settings
interface for configuring search preferences, UI preferences, and performance settings.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional  # noqa: F401

from loguru import logger
from PyQt6.QtCore import Qt, QTimer  # noqa: F401
from PyQt6.QtWidgets import QComboBox  # noqa: F401
from PyQt6.QtWidgets import QListWidgetItem  # noqa: F401
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QDialogButtonBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.exceptions import ConfigError  # noqa: F401
from filesearch.plugins.plugin_manager import PluginManager


class SettingsDialog(QDialog):
    """Settings dialog for configuring application preferences.

    This class implements a tabbed interface for configuring:
    - Search preferences (directories, case sensitivity, file exclusions)
    - UI preferences (window geometry, font size, display options)
    - Performance settings (thread count, caching)

    Attributes:
        config_manager (ConfigManager): Configuration manager instance
        tabs (QTabWidget): Tab widget containing all settings tabs
        search_tab (QWidget): Search preferences tab
        ui_tab (QWidget): UI preferences tab
        performance_tab (QWidget): Performance settings tab
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

    def setup_ui(self) -> None:
        """Setup the user interface."""
        # Create main layout
        main_layout = QVBoxLayout()
        self.setLayout(main_layout)

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create tabs
        self.search_tab = self._create_search_tab()
        self.ui_tab = self._create_ui_tab()
        self.performance_tab = self._create_performance_tab()
        if self.plugin_manager:
            self.plugin_tab = self._create_plugin_tab()

        # Add tabs to widget
        self.tabs.addTab(self.search_tab, "Search")
        self.tabs.addTab(self.ui_tab, "UI")
        self.tabs.addTab(self.performance_tab, "Performance")
        if self.plugin_manager:
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

    def _create_search_tab(self) -> QWidget:
        """Create the search preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Default search directory
        dir_group = QGroupBox("Default Search Directory")
        dir_layout = QHBoxLayout()

        self.default_dir_input = QLineEdit()
        self.default_dir_input.setPlaceholderText("Enter directory path...")
        self.default_dir_browse = QPushButton("Browse...")
        self.default_dir_browse.clicked.connect(self.browse_default_directory)

        dir_layout.addWidget(self.default_dir_input)
        dir_layout.addWidget(self.default_dir_browse)
        dir_group.setLayout(dir_layout)
        layout.addWidget(dir_group)

        # Search options
        options_group = QGroupBox("Search Options")
        options_layout = QVBoxLayout()

        self.case_sensitive_check = QCheckBox("Case sensitive search")
        self.include_hidden_check = QCheckBox("Include hidden files")

        options_layout.addWidget(self.case_sensitive_check)
        options_layout.addWidget(self.include_hidden_check)
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)

        # Max results
        max_results_layout = QHBoxLayout()
        max_results_layout.addWidget(QLabel("Maximum search results:"))

        self.max_results_spin = QSpinBox()
        self.max_results_spin.setRange(1, 10000)
        self.max_results_spin.setSingleStep(100)
        max_results_layout.addWidget(self.max_results_spin)

        layout.addLayout(max_results_layout)

        # File extensions to exclude
        exclude_group = QGroupBox("File Extensions to Exclude")
        exclude_layout = QVBoxLayout()

        self.exclude_list = QListWidget()
        self.exclude_list.setMaximumHeight(100)
        exclude_layout.addWidget(self.exclude_list)

        # Add/remove extension controls
        ext_controls_layout = QHBoxLayout()
        self.new_ext_input = QLineEdit()
        self.new_ext_input.setPlaceholderText("Enter extension (e.g., .tmp)")
        self.add_ext_button = QPushButton("Add")
        self.add_ext_button.clicked.connect(self.add_extension)
        self.remove_ext_button = QPushButton("Remove Selected")
        self.remove_ext_button.clicked.connect(self.remove_extension)

        ext_controls_layout.addWidget(self.new_ext_input)
        ext_controls_layout.addWidget(self.add_ext_button)
        ext_controls_layout.addWidget(self.remove_ext_button)
        exclude_layout.addLayout(ext_controls_layout)

        exclude_group.setLayout(exclude_layout)
        layout.addWidget(exclude_group)

        layout.addStretch()
        return tab

    def _create_ui_tab(self) -> QWidget:
        """Create the UI preferences tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Window geometry
        geometry_group = QGroupBox("Window Geometry")
        geometry_layout = QGridLayout()

        self.window_x_spin = QSpinBox()
        self.window_x_spin.setRange(0, 10000)
        self.window_y_spin = QSpinBox()
        self.window_y_spin.setRange(0, 10000)
        self.window_width_spin = QSpinBox()
        self.window_width_spin.setRange(400, 4000)
        self.window_height_spin = QSpinBox()
        self.window_height_spin.setRange(300, 3000)

        geometry_layout.addWidget(QLabel("X position:"), 0, 0)
        geometry_layout.addWidget(self.window_x_spin, 0, 1)
        geometry_layout.addWidget(QLabel("Y position:"), 1, 0)
        geometry_layout.addWidget(self.window_y_spin, 1, 1)
        geometry_layout.addWidget(QLabel("Width:"), 2, 0)
        geometry_layout.addWidget(self.window_width_spin, 2, 1)
        geometry_layout.addWidget(QLabel("Height:"), 3, 0)
        geometry_layout.addWidget(self.window_height_spin, 3, 1)

        geometry_group.setLayout(geometry_layout)
        layout.addWidget(geometry_group)

        # Display options
        display_group = QGroupBox("Display Options")
        display_layout = QVBoxLayout()

        self.result_font_size_spin = QSpinBox()
        self.result_font_size_spin.setRange(8, 72)
        self.result_font_size_spin.setSuffix(" pt")

        font_layout = QHBoxLayout()
        font_layout.addWidget(QLabel("Result font size:"))
        font_layout.addWidget(self.result_font_size_spin)
        font_layout.addStretch()
        display_layout.addLayout(font_layout)

        self.show_file_icons_check = QCheckBox("Show file icons")
        self.auto_expand_results_check = QCheckBox("Auto-expand results")

        display_layout.addWidget(self.show_file_icons_check)
        display_layout.addWidget(self.auto_expand_results_check)

        display_group.setLayout(display_layout)
        layout.addWidget(display_group)

        layout.addStretch()
        return tab

    def _create_performance_tab(self) -> QWidget:
        """Create the performance settings tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Thread settings
        thread_group = QGroupBox("Thread Settings")
        thread_layout = QHBoxLayout()

        self.thread_count_spin = QSpinBox()
        self.thread_count_spin.setRange(1, 32)
        self.thread_count_spin.setSuffix(" threads")

        thread_layout.addWidget(QLabel("Search thread count:"))
        thread_layout.addWidget(self.thread_count_spin)
        thread_layout.addStretch()

        thread_group.setLayout(thread_layout)
        layout.addWidget(thread_group)

        # Cache settings
        cache_group = QGroupBox("Cache Settings")
        cache_layout = QVBoxLayout()

        self.enable_cache_check = QCheckBox("Enable search cache")
        self.enable_cache_check.toggled.connect(self.on_cache_toggled)

        cache_ttl_layout = QHBoxLayout()
        self.cache_ttl_spin = QSpinBox()
        self.cache_ttl_spin.setRange(1, 1440)  # 1 minute to 24 hours
        self.cache_ttl_spin.setSuffix(" minutes")
        self.cache_ttl_spin.setEnabled(False)

        cache_ttl_layout.addWidget(QLabel("Cache TTL:"))
        cache_ttl_layout.addWidget(self.cache_ttl_spin)
        cache_ttl_layout.addStretch()

        cache_layout.addWidget(self.enable_cache_check)
        cache_layout.addLayout(cache_ttl_layout)
        cache_group.setLayout(cache_layout)
        layout.addWidget(cache_group)

        layout.addStretch()
        return tab

    def _create_plugin_tab(self) -> QWidget:
        """Create the plugin management tab."""
        tab = QWidget()
        layout = QVBoxLayout()
        tab.setLayout(layout)

        # Plugin list
        plugin_group = QGroupBox("Loaded Plugins")
        plugin_layout = QVBoxLayout()

        self.plugin_list = QListWidget()
        self.plugin_list.setMaximumHeight(200)
        plugin_layout.addWidget(self.plugin_list)

        # Plugin controls
        controls_layout = QHBoxLayout()
        self.enable_plugin_button = QPushButton("Enable")
        self.disable_plugin_button = QPushButton("Disable")
        self.configure_plugin_button = QPushButton("Configure")

        self.enable_plugin_button.clicked.connect(self.enable_selected_plugin)
        self.disable_plugin_button.clicked.connect(self.disable_selected_plugin)
        self.configure_plugin_button.clicked.connect(self.configure_selected_plugin)

        controls_layout.addWidget(self.enable_plugin_button)
        controls_layout.addWidget(self.disable_plugin_button)
        controls_layout.addWidget(self.configure_plugin_button)
        controls_layout.addStretch()

        plugin_layout.addLayout(controls_layout)
        plugin_group.setLayout(plugin_layout)
        layout.addWidget(plugin_group)

        # Plugin status
        status_group = QGroupBox("Plugin Status")
        status_layout = QVBoxLayout()

        self.plugin_status_label = QLabel("No plugins loaded")
        status_layout.addWidget(self.plugin_status_label)

        status_group.setLayout(status_layout)
        layout.addWidget(status_group)

        layout.addStretch()
        return tab

    def load_settings(self) -> None:
        """Load current settings from configuration."""
        try:
            # Load search preferences
            self.default_dir_input.setText(
                self.config_manager.get(
                    "search_preferences.default_search_directory", ""
                )
            )
            self.case_sensitive_check.setChecked(
                self.config_manager.get(
                    "search_preferences.case_sensitive_search", False
                )
            )
            self.include_hidden_check.setChecked(
                self.config_manager.get(
                    "search_preferences.include_hidden_files", False
                )
            )
            self.max_results_spin.setValue(
                self.config_manager.get("search_preferences.max_search_results", 1000)
            )

            # Load file extensions to exclude
            extensions = self.config_manager.get(
                "search_preferences.file_extensions_to_exclude", []
            )
            self.exclude_list.clear()
            for ext in extensions:
                self.exclude_list.addItem(ext)

            # Load UI preferences
            window_geom = self.config_manager.get("ui_preferences.window_geometry", {})
            self.window_x_spin.setValue(window_geom.get("x", 100))
            self.window_y_spin.setValue(window_geom.get("y", 100))
            self.window_width_spin.setValue(window_geom.get("width", 800))
            self.window_height_spin.setValue(window_geom.get("height", 600))

            self.result_font_size_spin.setValue(
                self.config_manager.get("ui_preferences.result_font_size", 12)
            )
            self.show_file_icons_check.setChecked(
                self.config_manager.get("ui_preferences.show_file_icons", True)
            )
            self.auto_expand_results_check.setChecked(
                self.config_manager.get("ui_preferences.auto_expand_results", False)
            )

            # Load performance settings
            self.thread_count_spin.setValue(
                self.config_manager.get("performance_settings.search_thread_count", 4)
            )
            self.enable_cache_check.setChecked(
                self.config_manager.get(
                    "performance_settings.enable_search_cache", False
                )
            )
            self.cache_ttl_spin.setValue(
                self.config_manager.get("performance_settings.cache_ttl_minutes", 30)
            )

            # Load plugin settings
            if self.plugin_manager:
                self.load_plugin_settings()

            logger.debug("Settings loaded successfully")

        except Exception as e:
            logger.error(f"Error loading settings: {e}")
            QMessageBox.warning(self, "Load Error", f"Error loading settings: {e}")

    def save_settings(self) -> None:
        """Save current settings to configuration."""
        try:
            # Save search preferences
            self.config_manager.set(
                "search_preferences.default_search_directory",
                self.default_dir_input.text(),
            )
            self.config_manager.set(
                "search_preferences.case_sensitive_search",
                self.case_sensitive_check.isChecked(),
            )
            self.config_manager.set(
                "search_preferences.include_hidden_files",
                self.include_hidden_check.isChecked(),
            )
            self.config_manager.set(
                "search_preferences.max_search_results", self.max_results_spin.value()
            )

            # Save file extensions to exclude
            extensions = []
            for i in range(self.exclude_list.count()):
                extensions.append(self.exclude_list.item(i).text())
            self.config_manager.set(
                "search_preferences.file_extensions_to_exclude", extensions
            )

            # Save UI preferences
            window_geom = {
                "x": self.window_x_spin.value(),
                "y": self.window_y_spin.value(),
                "width": self.window_width_spin.value(),
                "height": self.window_height_spin.value(),
            }
            self.config_manager.set("ui_preferences.window_geometry", window_geom)
            self.config_manager.set(
                "ui_preferences.result_font_size", self.result_font_size_spin.value()
            )
            self.config_manager.set(
                "ui_preferences.show_file_icons", self.show_file_icons_check.isChecked()
            )
            self.config_manager.set(
                "ui_preferences.auto_expand_results",
                self.auto_expand_results_check.isChecked(),
            )

            # Save performance settings
            self.config_manager.set(
                "performance_settings.search_thread_count",
                self.thread_count_spin.value(),
            )
            self.config_manager.set(
                "performance_settings.enable_search_cache",
                self.enable_cache_check.isChecked(),
            )
            self.config_manager.set(
                "performance_settings.cache_ttl_minutes", self.cache_ttl_spin.value()
            )

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

    def browse_default_directory(self) -> None:
        """Open directory browser for default search directory."""
        try:
            from PyQt6.QtWidgets import QFileDialog

            current_dir = self.default_dir_input.text()
            if not current_dir:
                current_dir = str(Path.home())

            directory = QFileDialog.getExistingDirectory(
                self, "Select Default Search Directory", current_dir
            )

            if directory:
                self.default_dir_input.setText(directory)

        except Exception as e:
            logger.error(f"Error browsing directory: {e}")
            QMessageBox.warning(self, "Browse Error", f"Error browsing directory: {e}")

    def add_extension(self) -> None:
        """Add a file extension to the exclude list."""
        ext = self.new_ext_input.text().strip()
        if ext:
            # Validate extension format
            if not ext.startswith("."):
                ext = "." + ext

            # Check for duplicates
            for i in range(self.exclude_list.count()):
                if self.exclude_list.item(i).text().lower() == ext.lower():
                    QMessageBox.warning(
                        self, "Duplicate Extension", f"Extension {ext} already exists."
                    )
                    self.new_ext_input.clear()
                    return

            self.exclude_list.addItem(ext)
            self.new_ext_input.clear()

        logger.debug(f"Added extension to exclude list: {ext}")

    def remove_extension(self) -> None:
        """Remove selected file extension from the exclude list."""
        current_row = self.exclude_list.currentRow()
        if current_row >= 0:
            self.exclude_list.takeItem(current_row)
            logger.debug("Removed extension from exclude list")

    def on_cache_toggled(self, checked: bool) -> None:
        """Handle cache enable/disable toggle."""
        self.cache_ttl_spin.setEnabled(checked)
        logger.debug(f"Cache toggled: {checked}")

    def load_plugin_settings(self) -> None:
        """Load plugin settings into the plugin tab."""
        if not self.plugin_manager:
            return

        self.plugin_list.clear()
        plugin_status = self.plugin_manager.get_plugin_status()

        for plugin_name, status in plugin_status.items():
            item_text = f"{plugin_name} - {status['name']} ({status['version']})"
            if status["loaded"]:
                item_text += " [Loaded]"
                if status["enabled"]:
                    item_text += " [Enabled]"
                else:
                    item_text += " [Disabled]"
            else:
                item_text += " [Not Loaded]"

            item = QListWidgetItem(item_text)
            item.setData(Qt.ItemDataRole.UserRole, plugin_name)
            self.plugin_list.addItem(item)

        # Update status label
        loaded_count = sum(1 for s in plugin_status.values() if s["loaded"])
        enabled_count = sum(
            1 for s in plugin_status.values() if s["loaded"] and s["enabled"]
        )
        self.plugin_status_label.setText(
            f"Loaded: {loaded_count}, Enabled: {enabled_count}"
        )

    def enable_selected_plugin(self) -> None:
        """Enable the selected plugin."""
        current_item = self.plugin_list.currentItem()
        if current_item and self.plugin_manager:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            if self.plugin_manager.enable_plugin(plugin_name):
                self.load_plugin_settings()
                logger.info(f"Enabled plugin: {plugin_name}")
            else:
                QMessageBox.warning(
                    self, "Enable Failed", f"Failed to enable plugin: {plugin_name}"
                )

    def disable_selected_plugin(self) -> None:
        """Disable the selected plugin."""
        current_item = self.plugin_list.currentItem()
        if current_item and self.plugin_manager:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            if self.plugin_manager.disable_plugin(plugin_name):
                self.load_plugin_settings()
                logger.info(f"Disabled plugin: {plugin_name}")
            else:
                QMessageBox.warning(
                    self, "Disable Failed", f"Failed to disable plugin: {plugin_name}"
                )

    def configure_selected_plugin(self) -> None:
        """Configure the selected plugin."""
        current_item = self.plugin_list.currentItem()
        if current_item and self.plugin_manager:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
                # For now, show a simple config dialog
                # In future, this could be more sophisticated
                config = plugin.config
                config_str = "\n".join(f"{k}: {v}" for k, v in config.items())
                QMessageBox.information(
                    self,
                    f"Plugin Config: {plugin_name}",
                    config_str or "No configuration",
                )
            else:
                QMessageBox.warning(
                    self, "Plugin Not Loaded", f"Plugin {plugin_name} is not loaded"
                )
