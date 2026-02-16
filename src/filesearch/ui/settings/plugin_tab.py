"""Plugin management tab for the settings dialog."""

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.plugins.plugin_manager import PluginManager


class PluginSettingsTab(QWidget):
    """Plugin management tab widget."""

    def __init__(self, plugin_manager: PluginManager, parent=None):
        super().__init__(parent)
        self.plugin_manager = plugin_manager
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the plugin tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

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

    def load_settings(self) -> None:
        """Load plugin settings into the plugin tab."""
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
        if current_item:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            if self.plugin_manager.enable_plugin(plugin_name):
                self.load_settings()
                logger.info(f"Enabled plugin: {plugin_name}")
            else:
                QMessageBox.warning(
                    self, "Enable Failed", f"Failed to enable plugin: {plugin_name}"
                )

    def disable_selected_plugin(self) -> None:
        """Disable the selected plugin."""
        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            if self.plugin_manager.disable_plugin(plugin_name):
                self.load_settings()
                logger.info(f"Disabled plugin: {plugin_name}")
            else:
                QMessageBox.warning(
                    self, "Disable Failed", f"Failed to disable plugin: {plugin_name}"
                )

    def configure_selected_plugin(self) -> None:
        """Configure the selected plugin."""
        current_item = self.plugin_list.currentItem()
        if current_item:
            plugin_name = current_item.data(Qt.ItemDataRole.UserRole)
            plugin = self.plugin_manager.get_plugin(plugin_name)
            if plugin:
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
