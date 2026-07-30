"""Tests for application-level theme behavior."""

import pytest
from PyQt6.QtCore import QPoint
from PyQt6.QtWidgets import QApplication, QToolTip

from filesearch.ui.theme import apply_theme


@pytest.mark.ui
def test_global_theme_renders_compact_tooltip_padding(qapp: QApplication) -> None:
    """A themed tooltip keeps its visible text container compact."""
    original_stylesheet = qapp.styleSheet()
    original_font = qapp.font()
    original_palette = qapp.palette()

    try:
        apply_theme(qapp)
        QToolTip.showText(QPoint(20, 20), "Filename: document.txt\nPath: /files")
        qapp.processEvents()

        tooltip = next(
            widget
            for widget in QApplication.topLevelWidgets()
            if widget.objectName() == "qtooltip_label"
        )
        margins = tooltip.contentsMargins()

        assert (
            margins.left(),
            margins.top(),
            margins.right(),
            margins.bottom(),
        ) == (7, 4, 7, 4)
    finally:
        QToolTip.hideText()
        qapp.setStyleSheet(original_stylesheet)
        qapp.setFont(original_font)
        qapp.setPalette(original_palette)
        qapp.processEvents()
