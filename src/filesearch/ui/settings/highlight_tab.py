"""Highlighting preferences tab for the settings dialog."""

from loguru import logger
from PyQt6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager


class HighlightSettingsTab(QWidget):
    """Highlighting preferences tab widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the highlighting tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

        # Highlighting options
        highlight_group = QGroupBox("Highlighting Options")
        highlight_layout = QVBoxLayout()

        self.highlight_enabled_check = QCheckBox("Enable search result highlighting")
        highlight_layout.addWidget(self.highlight_enabled_check)

        self.highlight_case_sensitive_check = QCheckBox("Case-sensitive highlighting")
        highlight_layout.addWidget(self.highlight_case_sensitive_check)

        highlight_group.setLayout(highlight_layout)
        layout.addWidget(highlight_group)

        # Highlight color
        color_group = QGroupBox("Highlight Color")
        color_layout = QHBoxLayout()

        self.highlight_color_input = QLineEdit()
        self.highlight_color_input.setPlaceholderText("#FFFF99")
        self.highlight_color_input.setMaximumWidth(100)

        self.highlight_color_button = QPushButton("Choose Color...")
        self.highlight_color_button.clicked.connect(self.choose_highlight_color)

        color_layout.addWidget(QLabel("Color (hex):"))
        color_layout.addWidget(self.highlight_color_input)
        color_layout.addWidget(self.highlight_color_button)
        color_layout.addStretch()

        color_group.setLayout(color_layout)
        layout.addWidget(color_group)

        # Highlight style
        style_group = QGroupBox("Highlight Style")
        style_layout = QVBoxLayout()

        self.highlight_style_combo = QComboBox()
        self.highlight_style_combo.addItems(["Background", "Outline", "Underline"])
        self.highlight_style_combo.setToolTip(
            "Choose how matching text is highlighted in search results"
        )

        style_layout.addWidget(QLabel("Style:"))
        style_layout.addWidget(self.highlight_style_combo)

        style_group.setLayout(style_layout)
        layout.addWidget(style_group)

        # Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout()

        self.highlight_preview_label = QLabel("Example: MonthlyReport.pdf")
        self.highlight_preview_label.setMinimumHeight(40)

        preview_layout.addWidget(self.highlight_preview_label)

        preview_group.setLayout(preview_layout)
        layout.addWidget(preview_group)

        # Connect signals for live preview
        self.highlight_enabled_check.toggled.connect(self.update_highlight_preview)
        self.highlight_case_sensitive_check.toggled.connect(
            self.update_highlight_preview
        )
        self.highlight_color_input.textChanged.connect(self.update_highlight_preview)

        layout.addStretch()

    def load_settings(self, config_manager: ConfigManager) -> None:
        """Load highlight settings from configuration."""
        self.highlight_enabled_check.setChecked(
            config_manager.get("highlighting.enabled", True)
        )
        self.highlight_case_sensitive_check.setChecked(
            config_manager.get("highlighting.case_sensitive", False)
        )
        self.highlight_color_input.setText(
            config_manager.get("highlighting.color", "#FFFF99")
        )
        highlight_style = config_manager.get("highlighting.style", "background")
        style_index = {"background": 0, "outline": 1, "underline": 2}.get(
            highlight_style, 0
        )
        self.highlight_style_combo.setCurrentIndex(style_index)

        self.update_highlight_preview()

    def save_settings(self, config_manager: ConfigManager) -> None:
        """Save highlight settings to configuration."""
        config_manager.set(
            "highlighting.enabled", self.highlight_enabled_check.isChecked()
        )
        config_manager.set(
            "highlighting.case_sensitive",
            self.highlight_case_sensitive_check.isChecked(),
        )
        config_manager.set("highlighting.color", self.highlight_color_input.text())

        style_map = {0: "background", 1: "outline", 2: "underline"}
        highlight_style = style_map.get(
            self.highlight_style_combo.currentIndex(), "background"
        )
        config_manager.set("highlighting.style", highlight_style)

    def choose_highlight_color(self) -> None:
        """Open color picker dialog for highlight color."""
        try:
            from PyQt6.QtGui import QColor
            from PyQt6.QtWidgets import QColorDialog

            current_color = self.highlight_color_input.text()
            if not current_color.startswith("#") or len(current_color) != 7:
                current_color = "#FFFF99"  # Default yellow

            color = QColorDialog.getColor(
                QColor(current_color), self, "Choose Highlight Color"
            )

            if color.isValid():
                self.highlight_color_input.setText(color.name())

        except Exception as e:
            logger.error(f"Error choosing highlight color: {e}")
            QMessageBox.warning(
                self, "Color Picker Error", f"Error choosing color: {e}"
            )

    def update_highlight_preview(self) -> None:
        """Update the highlight preview label."""
        try:
            enabled = self.highlight_enabled_check.isChecked()
            color = self.highlight_color_input.text()

            if not enabled:
                self.highlight_preview_label.setText("Example: MonthlyReport.pdf")
                return

            if not color.startswith("#") or len(color) != 7:
                color = "#FFFF99"

            html_template = """
            <html>
            <body style="padding: 10px;">
                Example: Monthly<span style="background-color: {color};">
                Report</span>.pdf
            </body>
            </html>
            """
            preview_html = html_template.format(color=color)

            self.highlight_preview_label.setText(preview_html)

        except Exception as e:
            logger.error(f"Error updating highlight preview: {e}")
