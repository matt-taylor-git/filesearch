"""Search preferences tab for the settings dialog."""

from pathlib import Path

from loguru import logger
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager


class SearchSettingsTab(QWidget):
    """Search preferences tab widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the search tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

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

    def load_settings(self, config_manager: ConfigManager) -> None:
        """Load search settings from configuration."""
        self.default_dir_input.setText(
            config_manager.get("search_preferences.default_search_directory", "")
        )
        self.case_sensitive_check.setChecked(
            config_manager.get("search_preferences.case_sensitive_search", False)
        )
        self.include_hidden_check.setChecked(
            config_manager.get("search_preferences.include_hidden_files", False)
        )
        self.max_results_spin.setValue(
            config_manager.get("search_preferences.max_search_results", 1000)
        )

        extensions = config_manager.get(
            "search_preferences.file_extensions_to_exclude", []
        )
        self.exclude_list.clear()
        for ext in extensions:
            self.exclude_list.addItem(ext)

    def save_settings(self, config_manager: ConfigManager) -> None:
        """Save search settings to configuration."""
        config_manager.set(
            "search_preferences.default_search_directory",
            self.default_dir_input.text(),
        )
        config_manager.set(
            "search_preferences.case_sensitive_search",
            self.case_sensitive_check.isChecked(),
        )
        config_manager.set(
            "search_preferences.include_hidden_files",
            self.include_hidden_check.isChecked(),
        )
        config_manager.set(
            "search_preferences.max_search_results", self.max_results_spin.value()
        )

        extensions = []
        for i in range(self.exclude_list.count()):
            extensions.append(self.exclude_list.item(i).text())
        config_manager.set(
            "search_preferences.file_extensions_to_exclude", extensions
        )

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
            if not ext.startswith("."):
                ext = "." + ext

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
