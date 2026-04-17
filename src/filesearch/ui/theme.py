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
    """Application color palette — dark navy mode."""

    # Primary accent — vibrant blue
    PRIMARY = "#5B8DEF"
    PRIMARY_HOVER = "#4A7ADB"
    PRIMARY_LIGHT = "#1B2A4A"
    PRIMARY_SUBTLE = "#131C32"

    # Backgrounds — layered depth
    BG_PRIMARY = "#0D0F17"
    BG_SECONDARY = "#131620"
    BG_TERTIARY = "#1A1E2E"

    # Borders — subtle separation
    BORDER_DEFAULT = "#232840"
    BORDER_STRONG = "#2F3652"

    # Text — high-contrast on dark
    TEXT_PRIMARY = "#E2E5EE"
    TEXT_SECONDARY = "#858BA0"
    TEXT_TERTIARY = "#525973"

    # Status
    SUCCESS = "#34D399"
    ERROR = "#F87171"
    WARNING = "#FBBF24"

    # Highlight — warm amber on dark
    HIGHLIGHT_BG = "#C8911A"
    HIGHLIGHT_TEXT = "#FFF8E7"

    # Result items
    SIZE_PILL_BG = "#1A1E2E"
    ITEM_SELECTED_BG = "#1B2A4A"
    ITEM_HOVER_BG = "#171B28"
    ITEM_SEPARATOR = "#1C2030"

    # Stop button — red
    STOP = "#EF4444"
    STOP_HOVER = "#DC2626"
    STOP_PRESSED = "#B91C1C"

    # Disabled
    DISABLED_BG = "#1A1E2E"
    DISABLED_TEXT = "#3D4360"

    # Tag colors
    TAG_RED = "#F87171"
    TAG_BLUE = "#5B8DEF"
    TAG_GREEN = "#34D399"
    TAG_YELLOW = "#FBBF24"
    TAG_PURPLE = "#A78BFA"

    # File type icon colors
    FILE_DOC = "#5B8DEF"
    FILE_IMAGE = "#34D399"
    FILE_VIDEO = "#F87171"
    FILE_AUDIO = "#FBBF24"
    FILE_ARCHIVE = "#A78BFA"
    FILE_CODE = "#60A5FA"
    FILE_PDF = "#EF4444"
    FILE_FOLDER = "#FBBF24"

    # Storage visualization
    STORAGE_CARD = "#111827"
    STORAGE_CARD_ALT = "#172033"
    STORAGE_BLUE = "#4F8CF7"
    STORAGE_GREEN = "#39C89B"
    STORAGE_GOLD = "#D4A72C"
    STORAGE_CORAL = "#D8665A"


class Fonts:
    """Font configuration constants."""

    FAMILY = "Segoe UI, system-ui, -apple-system, sans-serif"
    FAMILY_MONO = "Consolas, Menlo, monospace"

    SIZE_XS = 8   # pt — metadata, timestamps
    SIZE_SM = 9   # pt — secondary text, paths
    SIZE_BASE = 10  # pt — body text, filenames
    SIZE_LG = 12  # pt — labels, headings
    SIZE_XL = 14  # pt — primary headings

    WEIGHT_NORMAL = 400
    WEIGHT_MEDIUM = 500
    WEIGHT_SEMIBOLD = 600
    WEIGHT_BOLD = 700


class Spacing:
    """Spacing and dimension constants."""

    # Margins & Padding
    MARGIN_MAIN = 16
    SPACING_MAIN = 12
    PADDING_INPUT = 10
    PADDING_ITEM = 12
    PADDING_PILL = 6

    # Radii — rounded modern feel
    RADIUS_SM = 6
    RADIUS_MD = 10
    RADIUS_LG = 12

    # Dimensions
    ITEM_HEIGHT = 64
    SCROLLBAR_WIDTH = 6
    SEPARATOR_HEIGHT = 1


# ---------------------------------------------------------------------------
# Complete application QSS stylesheet — dark navy mode
# ---------------------------------------------------------------------------
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
    color: {Colors.TEXT_SECONDARY};
}}

QMenuBar::item {{
    padding: 5px 10px;
    border-radius: {Spacing.RADIUS_SM}px;
    color: {Colors.TEXT_SECONDARY};
}}

QMenuBar::item:selected {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== Menus ===== */
QMenu {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    padding: 6px;
    font-size: {Fonts.SIZE_BASE}pt;
    color: {Colors.TEXT_PRIMARY};
}}

QMenu::item {{
    padding: 7px 28px 7px 14px;
    border-radius: {Spacing.RADIUS_SM}px;
    color: {Colors.TEXT_PRIMARY};
}}

QMenu::item:selected {{
    background-color: {Colors.PRIMARY_LIGHT};
    color: {Colors.PRIMARY};
}}

QMenu::item:disabled {{
    color: {Colors.DISABLED_TEXT};
}}

QMenu::separator {{
    height: 1px;
    background: {Colors.BORDER_DEFAULT};
    margin: 6px 10px;
}}

/* ===== Status Bar ===== */
QStatusBar {{
    background-color: {Colors.BG_SECONDARY};
    border-top: 1px solid {Colors.BORDER_DEFAULT};
    font-size: {Fonts.SIZE_XS}pt;
    color: {Colors.TEXT_TERTIARY};
    padding: 2px 8px;
}}

QStatusBar QLabel {{
    color: {Colors.TEXT_TERTIARY};
    font-size: {Fonts.SIZE_XS}pt;
    padding: 0 8px;
}}

/* ===== Labels ===== */
QLabel[class="search-label"],
QLabel[class="directory-label"] {{
    font-size: {Fonts.SIZE_SM}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_TERTIARY};
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
    color: {Colors.TEXT_TERTIARY};
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
    color: {Colors.TEXT_TERTIARY};
}}

/* ===== Line Edits ===== */
QLineEdit {{
    font-size: {Fonts.SIZE_BASE}pt;
    padding: {Spacing.PADDING_INPUT}px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
    background: {Colors.BG_SECONDARY};
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
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_SECONDARY};
    border-color: {Colors.BORDER_DEFAULT};
}}

/* ===== Push Buttons ===== */
QPushButton {{
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    border: 1.5px solid {Colors.PRIMARY};
    border-radius: {Spacing.RADIUS_SM}px;
    background-color: {Colors.PRIMARY};
    color: #FFFFFF;
    padding: 6px 16px;
}}

QPushButton:hover {{
    background-color: {Colors.PRIMARY_HOVER};
    border-color: {Colors.PRIMARY_HOVER};
}}

QPushButton:pressed {{
    background-color: #3A65B8;
    border-color: #3A65B8;
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

/* Ghost / secondary button variant */
QPushButton[class="ghost"] {{
    background-color: transparent;
    border-color: {Colors.BORDER_STRONG};
    color: {Colors.TEXT_SECONDARY};
}}

QPushButton[class="ghost"]:hover {{
    background-color: {Colors.BG_TERTIARY};
    border-color: {Colors.PRIMARY};
    color: {Colors.PRIMARY};
}}

/* ===== Tool Buttons ===== */
QToolButton {{
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_SECONDARY};
    font-weight: {Fonts.WEIGHT_BOLD};
    padding: 4px;
}}

QToolButton:hover {{
    background: {Colors.BG_TERTIARY};
    border-color: {Colors.BORDER_STRONG};
    color: {Colors.TEXT_PRIMARY};
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
    padding: 5px 10px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
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
    padding-right: 8px;
}}

QComboBox::down-arrow {{
    image: none;
    border: none;
}}

QComboBox QAbstractItemView {{
    background: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    selection-background-color: {Colors.PRIMARY_LIGHT};
    selection-color: {Colors.PRIMARY};
    padding: 4px;
    color: {Colors.TEXT_PRIMARY};
    outline: none;
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
    padding: 8px 18px;
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-bottom: none;
    border-top-left-radius: {Spacing.RADIUS_SM}px;
    border-top-right-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_TERTIARY};
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
    padding-top: 18px;
}}

QGroupBox::title {{
    subcontrol-origin: margin;
    left: 14px;
    padding: 0 8px;
    color: {Colors.TEXT_SECONDARY};
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
    border-radius: 4px;
    background: {Colors.BG_SECONDARY};
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
    padding: 5px 10px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_PRIMARY};
}}

QSpinBox:focus {{
    border-color: {Colors.PRIMARY};
}}

QSpinBox::up-button,
QSpinBox::down-button {{
    background: {Colors.BG_TERTIARY};
    border: none;
    border-radius: 3px;
    width: 18px;
}}

QSpinBox::up-button:hover,
QSpinBox::down-button:hover {{
    background: {Colors.BORDER_STRONG};
}}

/* ===== Dialog ===== */
QDialog {{
    background-color: {Colors.BG_PRIMARY};
}}

/* ===== Tooltips ===== */
QToolTip {{
    background-color: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
    border: 1px solid {Colors.BORDER_STRONG};
    border-radius: {Spacing.RADIUS_SM}px;
    padding: 6px 10px;
    font-size: {Fonts.SIZE_SM}pt;
}}

/* ===== List Widget (Settings) ===== */
QListWidget {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    font-size: {Fonts.SIZE_BASE}pt;
    color: {Colors.TEXT_PRIMARY};
}}

QListWidget::item {{
    padding: 5px 10px;
    border-radius: {Spacing.RADIUS_SM}px;
}}

QListWidget::item:selected {{
    background-color: {Colors.PRIMARY_LIGHT};
    color: {Colors.PRIMARY};
}}

QListWidget::item:hover:!selected {{
    background-color: {Colors.BG_TERTIARY};
}}

/* ===== Scroll Area (Properties Dialog) ===== */
QScrollArea {{
    background: {Colors.BG_PRIMARY};
    border: none;
}}

QScrollArea > QWidget > QWidget {{
    background: {Colors.BG_PRIMARY};
}}

/* ===== Form Layout Labels (Properties Dialog) ===== */
QFormLayout QLabel {{
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== Message Box ===== */
QMessageBox {{
    background-color: {Colors.BG_PRIMARY};
}}

QMessageBox QLabel {{
    color: {Colors.TEXT_PRIMARY};
}}

/* ===== File Dialog ===== */
QFileDialog {{
    background-color: {Colors.BG_PRIMARY};
}}

/* ===== Color Dialog ===== */
QColorDialog {{
    background-color: {Colors.BG_PRIMARY};
}}

/* ===== Input Dialog ===== */
QInputDialog {{
    background-color: {Colors.BG_PRIMARY};
}}

/* ===== Dialog Button Box ===== */
QDialogButtonBox QPushButton {{
    min-width: 80px;
}}

/* ===== Header Separator (visual divider) ===== */
QFrame[class="separator"] {{
    background: {Colors.BORDER_DEFAULT};
    max-height: 1px;
    border: none;
}}

/* ===== QSplitter ===== */
QSplitter::handle {{
    background: {Colors.BORDER_DEFAULT};
}}
QSplitter::handle:horizontal {{
    width: 1px;
}}

/* ===== Sidebar ===== */
QWidget#sidebarWidget {{
    background-color: {Colors.BG_SECONDARY};
    border-right: 1px solid {Colors.BORDER_DEFAULT};
}}

QLabel[class="sidebar-title"] {{
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
    color: {Colors.TEXT_PRIMARY};
    padding: 4px 0px;
}}

QLabel[class="sidebar-section"] {{
    font-size: {Fonts.SIZE_XS}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_TERTIARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
    padding: 4px 0px;
}}

QPushButton[class="sidebar-item"] {{
    text-align: left;
    padding: 8px 12px;
    border: none;
    border-radius: {Spacing.RADIUS_SM}px;
    background: transparent;
    color: {Colors.TEXT_SECONDARY};
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_NORMAL};
}}

QPushButton[class="sidebar-item"]:hover {{
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

QPushButton[class="sidebar-item"][active="true"] {{
    background: {Colors.PRIMARY_LIGHT};
    color: {Colors.PRIMARY};
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
}}

/* File type filter chips */
QPushButton[class="filter-chip"] {{
    padding: 5px 10px;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: 14px;
    background: transparent;
    color: {Colors.TEXT_SECONDARY};
    font-size: {Fonts.SIZE_XS}pt;
    font-weight: {Fonts.WEIGHT_MEDIUM};
}}

QPushButton[class="filter-chip"]:hover {{
    border-color: {Colors.BORDER_STRONG};
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

QPushButton[class="filter-chip"][active="true"] {{
    border-color: {Colors.PRIMARY};
    background: {Colors.PRIMARY_SUBTLE};
    color: {Colors.PRIMARY};
}}

/* Tag badges */
QPushButton[class="tag-badge"] {{
    padding: 3px 8px;
    border: none;
    border-radius: 10px;
    font-size: {Fonts.SIZE_XS}pt;
    font-weight: {Fonts.WEIGHT_MEDIUM};
    color: #FFFFFF;
}}

QPushButton[class="tag-badge"]:hover {{
    opacity: 0.8;
}}

/* Storage bar */
QProgressBar[class="storage-bar"] {{
    border: none;
    border-radius: 3px;
    background: {Colors.BG_TERTIARY};
    max-height: 6px;
}}

QProgressBar[class="storage-bar"]::chunk {{
    background: {Colors.PRIMARY};
    border-radius: 3px;
}}

QLabel[class="storage-text"] {{
    font-size: {Fonts.SIZE_XS}pt;
    color: {Colors.TEXT_TERTIARY};
}}

/* ===== Details Panel ===== */
QWidget#detailsPanel {{
    background-color: {Colors.BG_SECONDARY};
    border-left: 1px solid {Colors.BORDER_DEFAULT};
}}

QLabel[class="details-header"] {{
    font-size: {Fonts.SIZE_XS}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_TERTIARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QToolButton[class="details-close"] {{
    border: none;
    background: transparent;
    color: {Colors.TEXT_TERTIARY};
    border-radius: {Spacing.RADIUS_SM}px;
    padding: 4px;
}}

QToolButton[class="details-close"]:hover {{
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

QLabel[class="details-filename"] {{
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
    color: {Colors.TEXT_PRIMARY};
}}

QLabel[class="details-fileinfo"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

QPushButton[class="details-open"] {{
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    border: none;
    border-radius: {Spacing.RADIUS_SM}px;
    background-color: {Colors.PRIMARY};
    color: #FFFFFF;
    padding: 8px 16px;
}}

QPushButton[class="details-open"]:hover {{
    background-color: {Colors.PRIMARY_HOVER};
}}

QPushButton[class="details-action"] {{
    font-size: {Fonts.SIZE_SM}pt;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: transparent;
    color: {Colors.TEXT_SECONDARY};
    padding: 6px 10px;
}}

QPushButton[class="details-action"]:hover {{
    border-color: {Colors.BORDER_STRONG};
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_PRIMARY};
}}

QLabel[class="details-meta-label"] {{
    font-size: {Fonts.SIZE_XS}pt;
    color: {Colors.TEXT_TERTIARY};
}}

QLabel[class="details-meta-value"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

QPushButton[class="details-trash"] {{
    font-size: {Fonts.SIZE_SM}pt;
    border: none;
    background: transparent;
    color: {Colors.ERROR};
    padding: 6px 0px;
}}

QPushButton[class="details-trash"]:hover {{
    color: {Colors.STOP_HOVER};
}}

/* ===== Search Bar (redesigned) ===== */
QWidget#searchBarContainer {{
    background-color: {Colors.BG_SECONDARY};
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_MD}px;
}}

QWidget#searchBarContainer:focus-within {{
    border-color: {Colors.PRIMARY};
}}

QWidget#searchBarContainer QLineEdit {{
    border: none;
    background: transparent;
    padding: 8px 4px;
    font-size: {Fonts.SIZE_BASE}pt;
    color: {Colors.TEXT_PRIMARY};
}}

QWidget#searchBarContainer QLineEdit:focus {{
    border: none;
    background: transparent;
}}

/* ===== Center Panel ===== */
QWidget#centerPanel {{
    background-color: {Colors.BG_PRIMARY};
}}

QWidget#searchPage,
QWidget#storagePage {{
    background-color: {Colors.BG_PRIMARY};
}}

QPushButton[class="storage-refresh"] {{
    font-size: {Fonts.SIZE_SM}pt;
    border: 1.5px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_SECONDARY};
    color: {Colors.TEXT_PRIMARY};
    padding: 6px 12px;
}}

QPushButton[class="storage-refresh"]:hover {{
    border-color: {Colors.PRIMARY};
    background: {Colors.PRIMARY_SUBTLE};
}}

QPushButton[class="storage-refresh"]:disabled {{
    color: {Colors.DISABLED_TEXT};
    border-color: {Colors.BORDER_DEFAULT};
}}

QLabel[class="storage-root-path"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

QLabel[class="storage-status"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

QFrame[class="storage-card"] {{
    background-color: {Colors.BG_SECONDARY};
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_LG}px;
}}

QLabel[class="storage-metric-label"] {{
    font-size: {Fonts.SIZE_XS}pt;
    color: {Colors.TEXT_TERTIARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[class="storage-metric-value"] {{
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
    color: {Colors.TEXT_PRIMARY};
}}

QPushButton[class="storage-breadcrumb"] {{
    border: 1px solid {Colors.BORDER_DEFAULT};
    border-radius: {Spacing.RADIUS_SM}px;
    background: {Colors.BG_TERTIARY};
    color: {Colors.TEXT_SECONDARY};
    padding: 5px 10px;
    font-size: {Fonts.SIZE_SM}pt;
}}

QPushButton[class="storage-breadcrumb"]:hover {{
    color: {Colors.TEXT_PRIMARY};
    border-color: {Colors.BORDER_STRONG};
}}

QPushButton[class="storage-breadcrumb"]:disabled {{
    color: {Colors.DISABLED_TEXT};
}}

QLabel[class="storage-breadcrumb-divider"] {{
    color: {Colors.TEXT_TERTIARY};
    font-size: {Fonts.SIZE_SM}pt;
}}

QLabel[class="storage-empty-state"],
QLabel[class="storage-error-state"] {{
    font-size: {Fonts.SIZE_LG}pt;
    color: {Colors.TEXT_SECONDARY};
    padding: 24px;
}}

QLabel[class="storage-error-state"] {{
    color: {Colors.ERROR};
}}

QLabel[class="storage-detail-section"] {{
    font-size: {Fonts.SIZE_XS}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.TEXT_TERTIARY};
    text-transform: uppercase;
    letter-spacing: 0.5px;
}}

QLabel[class="storage-detail-name"] {{
    font-size: {Fonts.SIZE_LG}pt;
    font-weight: {Fonts.WEIGHT_BOLD};
    color: {Colors.TEXT_PRIMARY};
}}

QLabel[class="storage-detail-meta"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
}}

QLabel[class="storage-detail-size"] {{
    font-size: {Fonts.SIZE_BASE}pt;
    font-weight: {Fonts.WEIGHT_SEMIBOLD};
    color: {Colors.PRIMARY};
}}

QLabel[class="storage-detail-path"] {{
    font-size: {Fonts.SIZE_SM}pt;
    color: {Colors.TEXT_SECONDARY};
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

    # Configure palette for dark mode
    palette = app.palette()
    palette.setColor(QPalette.ColorRole.Window, QColor(Colors.BG_PRIMARY))
    palette.setColor(QPalette.ColorRole.WindowText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Base, QColor(Colors.BG_SECONDARY))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.Text, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(
        QPalette.ColorRole.PlaceholderText, QColor(Colors.TEXT_TERTIARY)
    )
    palette.setColor(QPalette.ColorRole.Highlight, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#FFFFFF"))
    palette.setColor(QPalette.ColorRole.ToolTipBase, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ToolTipText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.Button, QColor(Colors.BG_TERTIARY))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor(Colors.TEXT_PRIMARY))
    palette.setColor(QPalette.ColorRole.BrightText, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.Link, QColor(Colors.PRIMARY))
    palette.setColor(QPalette.ColorRole.LinkVisited, QColor(Colors.PRIMARY_HOVER))

    # Disabled colors
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.Text,
        QColor(Colors.DISABLED_TEXT),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.WindowText,
        QColor(Colors.DISABLED_TEXT),
    )
    palette.setColor(
        QPalette.ColorGroup.Disabled,
        QPalette.ColorRole.ButtonText,
        QColor(Colors.DISABLED_TEXT),
    )

    app.setPalette(palette)
