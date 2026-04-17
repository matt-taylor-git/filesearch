"""Storage visualization tab with treemap drill-down."""

from __future__ import annotations

from pathlib import Path

import qtawesome as qta
from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

from filesearch.core.config_manager import ConfigManager
from filesearch.core.storage_analyzer import StorageAnalyzer
from filesearch.models.storage_node import (
    StorageAnalysisResult,
    StorageNode,
    format_bytes,
)
from filesearch.ui.storage_treemap import StorageTreemapWidget
from filesearch.ui.storage_worker import StorageWorker
from filesearch.ui.theme import Colors


class StorageTabWidget(QWidget):
    """Storage page that visualizes the active folder."""

    def __init__(
        self,
        config_manager: ConfigManager,
        root_path: Path,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self.setObjectName("storagePage")
        self.config_manager = config_manager
        self.root_path = Path(root_path)
        self._analysis_result: StorageAnalysisResult | None = None
        self._current_node: StorageNode | None = None
        self._worker: StorageWorker | None = None
        self._node_index: dict[Path, StorageNode] = {}
        self._parent_index: dict[Path, Path | None] = {}

        self._setup_ui()
        self._root_path_label.setText(str(self.root_path))
        self._reset_summary()
        self._set_hover_node(None)
        self._set_placeholder(
            "Open the Storage tab to scan this folder.",
            "storage-empty-state",
        )
        self._status_label.setText("Storage scan pending")
        self._update_breadcrumbs()

    def has_analysis(self) -> bool:
        """Return whether the tab already has analysis data."""
        return self._analysis_result is not None

    def set_root_path(self, root_path: Path, refresh: bool = True) -> None:
        """Update the active root path and optionally refresh the analysis."""
        path = Path(root_path)
        if path == self.root_path and self._analysis_result is not None:
            return

        self.root_path = path
        self._root_path_label.setText(str(path))
        self._reset_summary()
        self._set_hover_node(None)

        if refresh:
            self._set_placeholder(
                "Scanning storage usage...",
                "storage-empty-state",
            )
            self.refresh()
            return

        self._set_placeholder(
            "Open the Storage tab to scan this folder.",
            "storage-empty-state",
        )
        self._status_label.setText("Storage scan pending")
        self._analysis_result = None
        self._current_node = None
        self._node_index.clear()
        self._parent_index.clear()
        self._treemap.clear()
        self._update_breadcrumbs()

    def refresh(self) -> None:
        """Trigger a fresh background scan."""
        self._stop_worker()

        if not self.root_path.exists() or not self.root_path.is_dir():
            self._analysis_result = None
            self._current_node = None
            self._node_index.clear()
            self._parent_index.clear()
            self._treemap.clear()
            self._set_placeholder(
                "Select a valid folder to inspect storage.",
                "storage-empty-state",
            )
            self._status_label.setText("No storage data available")
            self._update_breadcrumbs()
            return

        self._analysis_result = None
        self._current_node = None
        self._node_index.clear()
        self._parent_index.clear()
        self._refresh_button.setEnabled(False)
        self._status_label.setText("Scanning storage usage...")
        self._set_placeholder("Scanning storage usage...", "storage-empty-state")

        analyzer = StorageAnalyzer(self.config_manager)
        self._worker = StorageWorker(analyzer, self.root_path)
        self._worker.progress_update.connect(self._on_progress_update)
        self._worker.analysis_complete.connect(self._on_analysis_complete)
        self._worker.analysis_error.connect(self._on_analysis_error)
        self._worker.analysis_cancelled.connect(self._on_analysis_cancelled)
        self._worker.start()
        logger.info(f"Storage refresh requested for {self.root_path}")

    def cleanup(self) -> None:
        """Stop background work when the main window closes."""
        self._stop_worker()

    def _setup_ui(self) -> None:
        """Build the storage page UI."""
        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self._scroll_area = QScrollArea()
        self._scroll_area.setWidgetResizable(True)
        self._scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        self._scroll_area.setHorizontalScrollBarPolicy(
            Qt.ScrollBarPolicy.ScrollBarAlwaysOff
        )
        outer.addWidget(self._scroll_area)

        content = QWidget()
        self._scroll_area.setWidget(content)

        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(16, 12, 16, 12)
        content_layout.setSpacing(12)

        header_row = QHBoxLayout()
        header_row.setSpacing(10)

        title = QLabel("STORAGE")
        title.setProperty("class", "results-header")
        header_row.addWidget(title)

        self._root_path_label = QLabel()
        self._root_path_label.setProperty("class", "storage-root-path")
        self._root_path_label.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        header_row.addWidget(self._root_path_label, 1)

        self._refresh_button = QPushButton(
            qta.icon("mdi6.refresh", color=Colors.TEXT_PRIMARY),
            " Refresh",
        )
        self._refresh_button.setProperty("class", "storage-refresh")
        self._refresh_button.clicked.connect(self.refresh)
        header_row.addWidget(self._refresh_button)
        content_layout.addLayout(header_row)

        self._status_label = QLabel("Storage scan pending")
        self._status_label.setProperty("class", "storage-status")
        content_layout.addWidget(self._status_label)

        self._summary_card = QFrame()
        self._summary_card.setProperty("class", "storage-card")
        summary_layout = QHBoxLayout(self._summary_card)
        summary_layout.setContentsMargins(16, 14, 16, 14)
        summary_layout.setSpacing(18)

        self._drive_used_value = self._add_metric(summary_layout, "Drive Used")
        self._drive_free_value = self._add_metric(summary_layout, "Drive Free")
        self._folder_size_value = self._add_metric(summary_layout, "Selected Folder")
        self._item_count_value = self._add_metric(summary_layout, "Items")
        self._skipped_count_value = self._add_metric(summary_layout, "Skipped")
        content_layout.addWidget(self._summary_card)

        self._breadcrumb_card = QFrame()
        self._breadcrumb_card.setProperty("class", "storage-card")
        self._breadcrumb_layout = QHBoxLayout(self._breadcrumb_card)
        self._breadcrumb_layout.setContentsMargins(12, 10, 12, 10)
        self._breadcrumb_layout.setSpacing(8)
        content_layout.addWidget(self._breadcrumb_card)

        content_row = QHBoxLayout()
        content_row.setSpacing(12)
        content_layout.addLayout(content_row)

        treemap_container = QFrame()
        treemap_container.setProperty("class", "storage-card")
        treemap_layout = QVBoxLayout(treemap_container)
        treemap_layout.setContentsMargins(10, 10, 10, 10)
        treemap_layout.setSpacing(0)

        self._treemap_stack = QStackedWidget()
        self._placeholder = QLabel()
        self._placeholder.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._placeholder.setWordWrap(True)

        self._treemap = StorageTreemapWidget()
        self._treemap.node_hovered.connect(self._set_hover_node)
        self._treemap.node_activated.connect(self._on_node_activated)

        self._treemap_stack.addWidget(self._placeholder)
        self._treemap_stack.addWidget(self._treemap)
        self._treemap_stack.setMinimumHeight(520)
        treemap_layout.addWidget(self._treemap_stack)
        content_row.addWidget(treemap_container, 1)

        self._detail_card = QFrame()
        self._detail_card.setProperty("class", "storage-card")
        self._detail_card.setFixedWidth(280)
        detail_layout = QVBoxLayout(self._detail_card)
        detail_layout.setContentsMargins(16, 16, 16, 16)
        detail_layout.setSpacing(8)

        detail_title = QLabel("DETAILS")
        detail_title.setProperty("class", "storage-detail-section")
        detail_layout.addWidget(detail_title)

        self._detail_name = QLabel("Hover a tile")
        self._detail_name.setProperty("class", "storage-detail-name")
        self._detail_name.setWordWrap(True)
        detail_layout.addWidget(self._detail_name)

        self._detail_type = QLabel("Storage details will appear here.")
        self._detail_type.setProperty("class", "storage-detail-meta")
        self._detail_type.setWordWrap(True)
        detail_layout.addWidget(self._detail_type)

        self._detail_size = QLabel("0 B")
        self._detail_size.setProperty("class", "storage-detail-size")
        detail_layout.addWidget(self._detail_size)

        path_title = QLabel("Path")
        path_title.setProperty("class", "storage-detail-section")
        detail_layout.addWidget(path_title)

        self._detail_path = QLabel("No node selected")
        self._detail_path.setProperty("class", "storage-detail-path")
        self._detail_path.setWordWrap(True)
        self._detail_path.setTextInteractionFlags(
            Qt.TextInteractionFlag.TextSelectableByMouse
        )
        detail_layout.addWidget(self._detail_path)
        detail_layout.addStretch()
        content_row.addWidget(self._detail_card)
        content_layout.addStretch()

    def _add_metric(self, layout: QHBoxLayout, label_text: str) -> QLabel:
        """Create one summary metric block and return its value label."""
        metric = QWidget()
        column = QVBoxLayout(metric)
        column.setContentsMargins(0, 0, 0, 0)
        column.setSpacing(4)

        label = QLabel(label_text)
        label.setProperty("class", "storage-metric-label")
        column.addWidget(label)

        value = QLabel("0")
        value.setProperty("class", "storage-metric-value")
        column.addWidget(value)

        layout.addWidget(metric)
        return value

    def _reset_summary(self) -> None:
        """Reset summary metric labels."""
        self._drive_used_value.setText("0 B")
        self._drive_free_value.setText("0 B")
        self._folder_size_value.setText("0 B")
        self._item_count_value.setText("0")
        self._skipped_count_value.setText("0")

    def _on_progress_update(
        self, current_path: str, item_count: int, skipped_count: int
    ) -> None:
        """Update header progress text."""
        path = Path(current_path)
        label = path.name or str(path)
        self._status_label.setText(
            f"Scanning {label} - {item_count} items - {skipped_count} skipped"
        )

    def _on_analysis_complete(self, result: StorageAnalysisResult) -> None:
        """Apply a completed storage analysis run."""
        self._worker = None
        self._refresh_button.setEnabled(True)
        self._analysis_result = result
        self._node_index.clear()
        self._parent_index.clear()
        self._index_tree(result.root, None)
        self._update_summary(result)
        self._show_node(result.root.path)
        self._status_label.setText(
            "Scanned {} items - {} skipped".format(
                result.summary.item_count, result.summary.skipped_count
            )
        )
        logger.info(f"Storage analysis applied for {result.summary.root_path}")

    def _on_analysis_error(self, message: str) -> None:
        """Display an analysis error."""
        self._worker = None
        self._refresh_button.setEnabled(True)
        self._treemap.clear()
        self._status_label.setText(f"Storage scan failed: {message}")
        self._set_placeholder(message, "storage-error-state")
        self._set_hover_node(None)
        logger.error(f"Storage tab error: {message}")

    def _on_analysis_cancelled(self) -> None:
        """Handle worker cancellation."""
        self._worker = None
        self._refresh_button.setEnabled(True)
        if self._analysis_result is None:
            self._status_label.setText("Storage scan cancelled")
            self._set_placeholder("Storage scan cancelled.", "storage-empty-state")
        logger.info("Storage analysis cancelled")

    def _update_summary(self, result: StorageAnalysisResult) -> None:
        """Update the metric card from the analysis result."""
        self._drive_used_value.setText(format_bytes(result.summary.drive_used))
        self._drive_free_value.setText(format_bytes(result.summary.drive_free))
        self._folder_size_value.setText(format_bytes(result.summary.total_size))
        self._item_count_value.setText(f"{result.summary.item_count:,}")
        self._skipped_count_value.setText(f"{result.summary.skipped_count:,}")

    def _show_node(self, path: Path) -> None:
        """Display the treemap for *path* if it exists in the node index."""
        node = self._node_index.get(path)
        if node is None:
            return

        self._current_node = node
        self._update_breadcrumbs()
        self._set_hover_node(None)

        if any(child.size > 0 for child in node.children):
            self._treemap.set_root_node(node)
            self._treemap_stack.setCurrentWidget(self._treemap)
        else:
            self._treemap.clear()
            self._set_placeholder(
                "Nothing sizeable to show in this folder.",
                "storage-empty-state",
            )

    def _update_breadcrumbs(self) -> None:
        """Rebuild breadcrumb buttons for the current node."""
        while self._breadcrumb_layout.count():
            item = self._breadcrumb_layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

        up_button = QPushButton(
            qta.icon("mdi6.arrow-up", color=Colors.TEXT_SECONDARY),
            " Up",
        )
        up_button.setProperty("class", "storage-breadcrumb")
        up_button.setEnabled(
            self._current_node is not None and self._current_node.path != self.root_path
        )
        up_button.clicked.connect(self._navigate_up)
        self._breadcrumb_layout.addWidget(up_button)

        if self._current_node is None:
            self._breadcrumb_layout.addStretch()
            return

        path_chain = []
        current_path = self._current_node.path
        while current_path is not None:
            path_chain.append(current_path)
            current_path = self._parent_index.get(current_path)
        path_chain.reverse()

        for index, path in enumerate(path_chain):
            button = QPushButton(self._breadcrumb_label(path))
            button.setProperty("class", "storage-breadcrumb")
            button.clicked.connect(lambda checked=False, p=path: self._show_node(p))
            self._breadcrumb_layout.addWidget(button)

            if index < len(path_chain) - 1:
                divider = QLabel(">")
                divider.setProperty("class", "storage-breadcrumb-divider")
                self._breadcrumb_layout.addWidget(divider)

        self._breadcrumb_layout.addStretch()

    def _breadcrumb_label(self, path: Path) -> str:
        """Return a short breadcrumb label."""
        if path == self.root_path:
            return path.name or path.drive or str(path)
        return path.name or str(path)

    def _navigate_up(self) -> None:
        """Navigate one level up in the breadcrumb chain."""
        if self._current_node is None:
            return

        parent_path = self._parent_index.get(self._current_node.path)
        if parent_path is not None:
            self._show_node(parent_path)

    def _on_node_activated(self, node: StorageNode) -> None:
        """Handle clicks inside the treemap."""
        if node.is_dir:
            self._show_node(node.path)
        else:
            self._set_hover_node(node)

    def _set_hover_node(self, node: StorageNode | None) -> None:
        """Populate the inline details panel from the hovered node."""
        target = node or self._current_node
        if target is None:
            self._detail_name.setText("Hover a tile")
            self._detail_type.setText("Storage details will appear here.")
            self._detail_size.setText("0 B")
            self._detail_path.setText("No node selected")
            return

        self._detail_name.setText(target.name)
        self._detail_type.setText("Folder" if target.is_dir else "File")
        self._detail_size.setText(format_bytes(target.size))
        self._detail_path.setText(str(target.path))

    def _set_placeholder(self, message: str, css_class: str) -> None:
        """Show the placeholder page with a themed message."""
        self._placeholder.setProperty("class", css_class)
        self._placeholder.style().unpolish(self._placeholder)
        self._placeholder.style().polish(self._placeholder)
        self._placeholder.setText(message)
        self._treemap_stack.setCurrentWidget(self._placeholder)

    def _index_tree(self, node: StorageNode, parent_path: Path | None) -> None:
        """Build path lookups for drill-down navigation."""
        self._node_index[node.path] = node
        self._parent_index[node.path] = parent_path
        for child in node.children:
            self._index_tree(child, node.path)

    def _stop_worker(self) -> None:
        """Stop any in-flight worker before launching another."""
        if self._worker is None:
            return

        worker = self._worker
        self._worker = None
        worker.stop()
        worker.wait()
