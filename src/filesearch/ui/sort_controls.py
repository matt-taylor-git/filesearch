"""Sort controls widget for search results"""

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QToolButton, QWidget

from ..core.sort_engine import SortCriteria


class SortControls(QWidget):
    """Widget providing sort controls for search results"""

    # Signal emitted when sort criteria changes
    sortChanged = pyqtSignal(SortCriteria)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._connect_signals()

    def _setup_ui(self):
        """Setup the UI components"""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        # Label
        self.sort_label = QLabel("Sort by:")
        layout.addWidget(self.sort_label)

        # Sort criteria dropdown
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Name (A-Z)", SortCriteria.NAME_ASC)
        self.sort_combo.addItem("Name (Z-A)", SortCriteria.NAME_DESC)
        self.sort_combo.addItem("Size (Smallest)", SortCriteria.SIZE_ASC)
        self.sort_combo.addItem("Size (Largest)", SortCriteria.SIZE_DESC)
        self.sort_combo.addItem("Date (Newest)", SortCriteria.DATE_DESC)
        self.sort_combo.addItem("Date (Oldest)", SortCriteria.DATE_ASC)
        self.sort_combo.addItem("Type", SortCriteria.TYPE_ASC)
        self.sort_combo.addItem("Relevance", SortCriteria.RELEVANCE_DESC)
        layout.addWidget(self.sort_combo)

        # Reverse sort button
        self.reverse_button = QToolButton()
        self.reverse_button.setText("⇅")
        self.reverse_button.setToolTip("Reverse sort order")
        layout.addWidget(self.reverse_button)

        # Visual indicator of current sort
        self._update_visual_indicator()

        layout.addStretch()

    def _connect_signals(self):
        """Connect signals to slots"""
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        self.reverse_button.clicked.connect(self._on_reverse_clicked)

    def _on_sort_changed(self, index):
        """Handle sort criteria change"""
        criteria = self.sort_combo.currentData()
        self.sortChanged.emit(criteria)
        self._update_visual_indicator()

    def _on_reverse_clicked(self):
        """Handle reverse button click"""
        current_criteria = self.sort_combo.currentData()

        # Map to reverse criteria
        reverse_map = {
            SortCriteria.NAME_ASC: SortCriteria.NAME_DESC,
            SortCriteria.NAME_DESC: SortCriteria.NAME_ASC,
            SortCriteria.SIZE_ASC: SortCriteria.SIZE_DESC,
            SortCriteria.SIZE_DESC: SortCriteria.SIZE_ASC,
            SortCriteria.DATE_ASC: SortCriteria.DATE_DESC,
            SortCriteria.DATE_DESC: SortCriteria.DATE_ASC,
        }

        if current_criteria in reverse_map:
            reverse_criteria = reverse_map[current_criteria]
            # Update combo box
            index = self.sort_combo.findData(reverse_criteria)
            if index >= 0:
                self.sort_combo.setCurrentIndex(index)

        self._update_visual_indicator()

    def _update_visual_indicator(self):
        """Update visual indicator showing current sort direction"""
        criteria = self.sort_combo.currentData()
        if criteria:
            # Update button icon/text based on direction
            if criteria in [SortCriteria.NAME_DESC, SortCriteria.SIZE_DESC, SortCriteria.DATE_ASC]:
                self.reverse_button.setText("⬇")
            else:
                self.reverse_button.setText("⬆")

    def set_criteria(self, criteria: SortCriteria):
        """Set the current sort criteria programmatically"""
        index = self.sort_combo.findData(criteria)
        if index >= 0:
            self.sort_combo.setCurrentIndex(index)

    def get_criteria(self) -> SortCriteria:
        """Get the current sort criteria"""
        return self.sort_combo.currentData()
