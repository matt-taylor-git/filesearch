"""Performance settings tab for the settings dialog."""

from loguru import logger
from PyQt6.QtWidgets import (
    QCheckBox,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager


class PerformanceSettingsTab(QWidget):
    """Performance settings tab widget."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the performance tab UI."""
        layout = QVBoxLayout()
        self.setLayout(layout)

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

    def on_cache_toggled(self, checked: bool) -> None:
        """Handle cache enable/disable toggle."""
        self.cache_ttl_spin.setEnabled(checked)
        logger.debug(f"Cache toggled: {checked}")

    def load_settings(self, config_manager: ConfigManager) -> None:
        """Load performance settings from configuration."""
        self.thread_count_spin.setValue(
            config_manager.get("performance_settings.search_thread_count", 4)
        )
        self.enable_cache_check.setChecked(
            config_manager.get("performance_settings.enable_search_cache", False)
        )
        self.cache_ttl_spin.setValue(
            config_manager.get("performance_settings.cache_ttl_minutes", 30)
        )

    def save_settings(self, config_manager: ConfigManager) -> None:
        """Save performance settings to configuration."""
        config_manager.set(
            "performance_settings.search_thread_count",
            self.thread_count_spin.value(),
        )
        config_manager.set(
            "performance_settings.enable_search_cache",
            self.enable_cache_check.isChecked(),
        )
        config_manager.set(
            "performance_settings.cache_ttl_minutes", self.cache_ttl_spin.value()
        )
