"""Centralized theme system for the File Search application.

This module provides the complete design system including colors, fonts, spacing,
and a QSS stylesheet. All visual styling is defined here to ensure consistency
across the application. Individual widgets should NOT use inline setStyleSheet()
calls; instead, they should use setProperty("class", ...) for variant styling
that is picked up by the centralized QSS.

Usage:
    from filesearch.ui.theme import apply_theme
    apply_theme(app)
"""

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont, QPalette
from PyQt6.QtWidgets import QApplication


class Colors:
    """Application color palette constants."""

    # Primary
    PRIMARY = "#2563EB"
    PRIMARY_HOVER = "#1D4ED8"
    PRIMARY_LIGHT = "#DBEAFE"
    PRIMARY_SUBTLE = "#EFF6FF"

    # Backgrounds
    BG_PRIMARY = "#FFFFFF"
    BG_SECONDARY = "#F8FAFC"
    BG_TERTIARY = "#F1F5F9"

    # Borders
    BORDER_DEFAULT = "#E2E8F0"
    BORDER_STRONG = "#CBD5E1"

    # Text
    TEXT_PRIMARY = "#0F172A"
    TEXT_SECONDARY = "#475569"
    TEXT_TERTIARY = "#94A3B8"

    # Status
    SUCCESS = "#059669"
    ERROR = "#DC2626"
    WARNING = "#D97706"

    # Highlight
    HIGHLIGHT_BG = "#FDE68A"
    HIGHLIGHT_TEXT = "#92400E"

    # Result items
    SIZE_PILL_BG = "#F1F5F9"
    ITEM_SELECTED_BG = "#DBEAFE"
    ITEM_HOVER_BG = "#F1F5F9"
    ITEM_SEPARATOR = "#E2E8F0"

    # Stop button
    STOP = "#DC2626"
    STOP_HOVER = "#B91C1C"
    STOP_PRESSED = "#991B1B"

    # Disabled
    DISABLED_BG = "#E2E8F0"
    DISABLED_TEXT = "#94A3B8"


class Fonts:
    """Font configuration constants."""

    FAMILY = "Segoe UI, system-ui, -apple-system, sans-serif"
    FAMILY_MONO = "Consolas, Menlo, monospace"

    SIZE_XS = 8  # pt - metadata, timestamps
    SIZE_SM = 9  # pt - secondary text, paths
    SIZE_BASE = 10  # pt - body text, filenames
    SIZE_LG = 12  # pt - labels, headings
    SIZE_XL = 14  # pt - primary headings

    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


class Spacing:
    """Spacing and dimension constants."""

    # Margins & Padding
    MARGIN_MAIN = 16  # Main window margins
    SPACING_MAIN = 12  # Main layout spacing
    PADDING_INPUT = 8  # Input field padding
    PADDING_ITEM = 12  # Result item padding
    PADDING_PILL = 6  # Pill horizontal padding

    # Radii
    RADIUS_SM = 4  # Small radius (pills, buttons)
    RADIUS_MD = 6  # Medium radius (inputs, cards)
    RADIUS_LG = 8  # Large radius (containers)

    # Dimensions
    ITEM_HEIGHT = 64  # Result item height
    SCROLLBAR_WIDTH = 6  # Thin scrollbar
    SEPARATOR_HEIGHT = 1  # Item separator line


# Complete application QSS stylesheet
APP_STYLESHEET = f"""
/* ===== Global ===== */
QMainWindow {{
    background-color: {Colors.BG_PRIMARY};
}}

QWidget {{
    font-family: {Fonts.FAMILY};
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== Menu Bar ===== */
QMenuBar {{
    background-color: {Colors.BG_PRIMARY};
    border-bottom: 1px solid {Colors.BORDER_DEFAULT};
    padding: 2px 4px;
    font-size: {Fonts.SIZE_BASE}pt;
}}

QMenuBar::item {{
    padding: 4px 8px;
    border-radius: {Spacing.RADIUS_SM}px;
}}

QMenuBar::item:selected {{
    background-color: {Colors.BG_TERTIARY};
}}

/* ===== Menus ===== */
QMenu {{
    background-color: {Colors.BG_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    padding: 4px;
    font-size: {Fonts.SIZE_BASE}pt;
}}

QMenu::item {{
    padding: 6px 24px 6px 12px;
    border-radius: {Spacing.RADIUS_SM}px;
}}

QMenu::item:selected {{
    background-color: {Colors.PRIMARY_LIGHT};
    color: {Colors.PRIMARY};
}}

QMenu::separator {{
    height: 1px;
    background: {Colors.BORDER_DEFAULT};
    margin: 4px 8px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {Colors.BG_SECONDARY};
    border-top: 1px solid {Colors.BORDER_DEFAULT};
    font-size: {Fonts.SIZE_XS}pt;
    color: {Colors.TEXT_SECONDARY};
    padding: 2px 8px;
}}

QStatusBar QLabel {{
    color: {Colors.TEXT_SECONDARY};
    font-size: {Fonts.SIZE_XS}pt;
    padding: 0 8px;
}}

/* ===== Labels ===== */
QLabel[class="search-label"],
QLabel[class="directory-label"] {{
    font-size: {Fonts.SIZE_SM}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    margin-bottom: 2px;
}}

QLabel[class="results-count"] {{
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
    color: {Colors.TEXT_SECONDARY};
}}

QLabel[class="results-count"][state="success"] {{
    color: {Colors.SUCCESS};
}}

QLabel[class="results-count"][state="zero"] {{
    color: {Colors.WARNING};
}}

QLabel[class="results-count"][state="error"] {{
    color: {Colors.ERROR};
}}

QLabel[class="status-summary"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_TERTIARY};
}}

QLabel[class="results-header"] {{
    font-size: {Fonts.SIZE_SM}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_SECONDARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[class="spinner"] {{
    color: {Colors.PRIMARY};
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
}}

QLabel[class="progress-text"] {{
    color: {Colors.TEXT_SECONDARY};
    font-size: {Fonts.SIZE_SM}pt;
}}

QLabel[class="file-counter"] {{
    color: {Colors.TEXT_SECONDARY};
    font-size: {Fonts.SIZE_SM}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
}}

QLabel[class="loading-indicator"] {{
    color: {Colors.PRIMARY};
    font-size: {Fonts.SIZE_LG}pt;
}}

QLabel[class="sort-label"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

/* ===== Line Edits ===== */
QLineEdit {{
    font-size: {Fonts.SIZE_BASE}pt;
    padding: {Spacing.PADDING_INPUT}px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    background: {Colors.BG_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
    selection-background-color: {Colors.PRIMARY_LIGHT};
    selection-color: {Colors.PRIMARY};
}}

QLineEdit:hover {{
    border-color: {Colors.BORDER_STRONG};
}}

QLineEdit:focus {{
    border-color: {Colors.PRIMARY};
    background: {Colors.PRIMARY_SUBTLE};
}}

QLineEdit[state="error"] {{
    border-color: {Colors.ERROR};
}}

QLineEdit:read-only {{
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_SECONDARY};
}}

/* ===== Push Buttons ===== */
QPushButton {{
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    border: 1.5px solid {Colors.PRIMARY};
    border-radius: {Spacing.RADIUS_SM}px;
    background-color: {Colors.PRIMARY};
    color: white;
    padding: 6px 14px;
}}

QPushButton:hover {{
    background-color: {Colors.PRIMARY_HOVER};
    border-color: {Colors.PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: #1E40AF;
    border-color: #1E40AF;
}}

QPushButton:disabled {{
    background-color: {Colors.DISABLED_BG};
    border-color: {Colors.DISABLED_BG};
    color: {Colors.DISABLED_TEXT};
}}

QPushButton[state="stop"] {{
    background-color: {Colors.STOP};
    border-color: {Colors.STOP};
}}

QPushButton[state="stop"]:hover {{
    background-color: {Colors.STOP_HOVER};
    border-color: {Colors.STOP_HOVER};
}}

QPushButton[state="stop"]:pressed {{
    background-color: {Colors.STOP_PRESSED};
    border-color: {Colors.STOP_PRESSED};
}}

/* ===== Tool Buttons ===== */
QToolButton {{
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_PRIMARY};
    color: {Colors.TEXT_SECONDARY};
    font-weight: {Fonts.WEIGHT_BOLD};
    padding: 4px;
}}

QToolButton:hover {{
    background: {Colors.BG_TERTIARY};
    border-color: {Colors.BORDER_STRONG};
}}

QToolButton[class="clear-button"] {{
    border: none;
    background: transparent;
    color: {Colors.TEXT_TERTIARY};
    font-size: {Fonts.SIZE_LG}pt;
}}

QToolButton[class="clear-button"]:hover {{
    color: {Colors.TEXT_PRIMARY};
    background: {Colors.BG_TERTIARY};
    border-radius: {Spacing.RADIUS_SM}px;
}}

/* ===== Combo Box ===== */
QComboBox {{
    font-size: {Fonts.SIZE_BASE}pt;
    padding: 4px 8px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
    min-width: 120px;
}}

QComboBox:hover {{
    border-color: {Colors.BORDER_STRONG};
}}

QComboBox:focus {{
    border-color: {Colors.PRIMARY};
}}

QComboBox::drop-down {{
    border: none;
    padding-right: 6px;
}}

QComboBox QAbstractItemView {{
    background: {Colors.BG_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    selection-background-color: {Colors.PRIMARY_LIGHT};
    selection-color: {Colors.PRIMARY};
    padding: 4px;
}}

/* ===== Progress Bar ===== */
QProgressBar {{
    border: none;
    border-radius: 3px;
    background: {Colors.BG_TERTIARY};
    max-height: 6px;
}}

QProgressBar::chunk {{
    background: {Colors.PRIMARY};
    border-radius: 3px;
}}

/* ===== List View (Results) ===== */
QListView {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_LG}px;
    outline: none;
    padding: 4px;
}}

QListView::item {{
    border: none;
    border-radius: {Spacing.RADIUS_SM}px;
    padding: 0px;
}}

QListView::item:selected {{
    background-color: {Colors.ITEM_SELECTED_BG};
}}

QListView::item:hover:!selected {{
    background-color: {Colors.ITEM_HOVER_BG};
}}

/* ===== Scroll Bars ===== */
QScrollBar:vertical {{
    background: transparent;
    width: {Spacing.SCROLLBAR_WIDTH + 4}px;
    margin: 4px 0;
}}

QScrollBar::handle:vertical {{
    background: {Colors.BORDER_STRONG};
    border-radius: 3px;
    min-height: 30px;
}}

QScrollBar::handle:vertical:hover {{
    background: {Colors.TEXT_TERTIARY};
}}

QScrollBar::add-line:vertical,
QScrollBar::sub-line:vertical {{
    height: 0;
    border: none;
}}

QScrollBar::add-page:vertical,
QScrollBar::sub-page:vertical {{
    background: transparent;
}}

QScrollBar:horizontal {{
    background: transparent;
    height: {Spacing.SCROLLBAR_WIDTH + 4}px;
    margin: 0 4px;
}}

QScrollBar::handle:horizontal {{
    background: {Colors.BORDER_STRONG};
    border-radius: 3px;
    min-width: 30px;
}}

QScrollBar::handle:horizontal:hover {{
    background: {Colors.TEXT_TERTIARY};
}}

QScrollBar::add-line:horizontal,
QScrollBar::sub-line:horizontal {{
    width: 0;
    border: none;
}}

QScrollBar::add-page:horizontal,
QScrollBar::sub-page:horizontal {{
    background: transparent;
}}

/* ===== Tab Widget (Settings) ===== */
QTabWidget::pane {{
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    background: {Colors.BG_PRIMARY};
    top: -1px;
}}

QTabBar::tab {{
    font-size: {Fonts.SIZE_BASE}pt;
    padding: 8px 16px;
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-bottom: none;
    border-top-left-radius: {Spacing.RADIUS_SM}px;
    border-top-right-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_SECONDARY};
    margin-right: 2px;
}}

QTabBar::tab:selected {{
    background: {Colors.BG_PRIMARY};
    color: {Colors.PRIMARY};
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    border-bottom: 2px solid {Colors.PRIMARY};
}}

QTabBar::tab:hover:!selected {{
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== Group Box ===== */
QGroupBox {{
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    margin-top: 12px;
    padding-top: 16px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 12px;
    padding: 0 6px;
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== Check Box ===== */
QCheckBox {{
    font-size: {Fonts.SIZE_BASE}pt;
    color: {Colors.TEXT_PRIMARY};
    spacing: 8px;
}}

QCheckBox::indicator {{
    width: 16px;
    height: 16px;
    border: 1.5px solid {Colors.BORDER_STRONG};
    border-radius: 3px;
    background: {Colors.BG_PRIMARY};
}}

QCheckBox::indicator:checked {{
    background: {Colors.PRIMARY};
    border-color: {Colors.PRIMARY};
}}

QCheckBox::indicator:hover {{
    border-color: {Colors.PRIMARY};
}}

/* ===== Spin Box ===== */
QSpinBox {{
    font-size: {Fonts.SIZE_BASE}pt;
    padding: 4px 8px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_PRIMARY};
    color: {Colors.TEXT_PRIMARY};
}}

QSpinBox:focus {{
    border-color: {Colors.PRIMARY};
}}

/* ===== Dialog ===== */
QDialog {{
    background-color: {Colors.BG_PRIMARY};
}}

/* ===== Tooltips ===== */
QToolTip {{
    background-color: {Colors.TEXT_PRIMARY};
    color: {Colors.BG_PRIMARY};
    border: none;
    border-radius: {Spacing.RADIUS_SM}px;
    padding: 6px 10px;
    font-size: {Fonts.SIZE_SM}pt;
}}

/* ===== List Widget (Settings) ===== */
QListWidget {{
    background-color: {Colors.BG_PRIMARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    font-size: {Fonts.SIZE_BASE}pt;
}}

QListWidget::item {{
    padding: 4px 8px;
    border-radius: {Spacing.RADIUS_SM}px;
}}

QListWidget::item:selected {{
    background-color: {Colors.PRIMARY_LIGHT};
    color: {Colors.PRIMARY};
}}

QListWidget::item:hover:!selected {{
    background-color: {Colors.BG_TERTIARY};
}}

/* ===== Dialog Button Box ===== */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}
"""


def apply_theme(app: QApplication) -> None:
    """Apply the centralized theme to the application.

    This sets the global font, stylesheet, and palette for a consistent
    look across all widgets.

    Args:
        app: The QApplication instance to theme.
    """
    # Set application font
    font = QFont("Segoe UI", Fonts.SIZE_BASE)
    font.setStyleStrategy(QFont.StyleStrategy.PreferAntialias)
    app.setFont(font)

    # Set the global stylesheet
    app.setStyleSheet(APP_STYLESHEET)

    # Configure palette for better default colors
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.PlaceholderText, QColor(Colors.TEXT_TERTIARY))
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY_LIGHT))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.BG_PRIMARY))
    app.setPalette(palette)
