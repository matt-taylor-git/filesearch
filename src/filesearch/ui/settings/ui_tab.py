"""UI preferences tab for the settings dialog."""

from PyQt6.QtWidgets import (
    QCheckBox,
    QGridLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager


class UISettingsTab(QWidget):
    """UI preferences tab widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the UI tab."""
        layout = QVBoxLayout()
        self.setLayout(layout)

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

    def load_settings(self, config_manager: ConfigManager) -> None:
        """Load UI settings from configuration."""
        window_geom = config_manager.get("ui_preferences.window_geometry", {})
        self.window_x_spin.setValue(window_geom.get("x", 100))
        self.window_y_spin.setValue(window_geom.get("y", 100))
        self.window_width_spin.setValue(window_geom.get("width", 800))
        self.window_height_spin.setValue(window_geom.get("height", 600))

        self.result_font_size_spin.setValue(
            config_manager.get("ui_preferences.result_font_size", 12)
        )
        self.show_file_icons_check.setChecked(
            config_manager.get("ui_preferences.show_file_icons", True)
        )
        self.auto_expand_results_check.setChecked(
            config_manager.get("ui_preferences.auto_expand_results", False)
        )

    def save_settings(self, config_manager: ConfigManager) -> None:
        """Save UI settings to configuration."""
        window_geom = {
            "x": self.window_x_spin.value(),
            "y": self.window_y_spin.value(),
            "width": self.window_width_spin.value(),
            "height": self.window_height_spin.value(),
        }
        config_manager.set("ui_preferences.window_geometry", window_geom)
        config_manager.set(
            "ui_preferences.result_font_size", self.result_font_size_spin.value()
        )
        config_manager.set(
            "ui_preferences.show_file_icons", self.show_file_icons_check.isChecked()
        )
        config_manager.set(
            "ui_preferences.auto_expand_results",
            self.auto_expand_results_check.isChecked(),
        )
