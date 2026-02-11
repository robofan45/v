"""Catppuccin Mocha theme constants and global stylesheet.

Centralises every colour and the application-wide QSS so each widget
file only needs to import ``APP_STYLESHEET`` or individual colour tokens.
"""

# ── Catppuccin Mocha palette ──────────────────────────────────────────
BASE      = "#1e1e2e"
MANTLE    = "#181825"
CRUST     = "#11111b"
SURFACE0  = "#313244"
SURFACE1  = "#45475a"
SURFACE2  = "#585b70"
OVERLAY0  = "#6c7086"
OVERLAY1  = "#7f849c"
TEXT      = "#cdd6f4"
SUBTEXT0  = "#a6adc8"
SUBTEXT1  = "#bac2de"
BLUE      = "#89b4fa"
LAVENDER  = "#b4befe"
SKY       = "#89dceb"
TEAL      = "#94e2d5"
GREEN     = "#a6e3a1"
YELLOW    = "#f9e2af"
PEACH     = "#fab387"
RED       = "#f38ba8"
MAUVE     = "#cba6f7"
PINK      = "#f5c2e7"
ROSEWATER = "#f5e0dc"

# ── Score thresholds ─────────────────────────────────────────────────
SCORE_GOOD = 70
SCORE_WARN = 40


def score_color(score: int) -> str:
    """Return a Catppuccin colour based on the focus score."""
    if score >= SCORE_GOOD:
        return GREEN
    if score >= SCORE_WARN:
        return YELLOW
    return RED


# ── UI constants ─────────────────────────────────────────────────────
FONT_FAMILY = '"Segoe UI", "SF Pro Display", "Cantarell", "Noto Sans", sans-serif'
FADE_DURATION_MS = 200
POPUP_WIDTH = 420

# ── Global application stylesheet ─────────────────────────────────────
APP_STYLESHEET = f"""
/* ---- Base -------------------------------------------------------- */
QWidget {{
    font-family: {FONT_FAMILY};
    font-size: 13px;
    color: {TEXT};
}}

/* ---- Dialog / Window backgrounds --------------------------------- */
QDialog, QMainWindow {{
    background-color: {BASE};
}}

/* ---- Group boxes ------------------------------------------------- */
QGroupBox {{
    background-color: {MANTLE};
    border: 1px solid {SURFACE1};
    border-radius: 10px;
    margin-top: 14px;
    padding: 18px 14px 12px 14px;
    font-weight: 600;
    font-size: 13px;
    color: {BLUE};
}}
QGroupBox::title {{
    subcontrol-origin: margin;
    subcontrol-position: top left;
    left: 16px;
    padding: 0 6px;
    color: {BLUE};
}}

/* ---- Labels ------------------------------------------------------ */
QLabel {{
    color: {TEXT};
    background: transparent;
}}

/* ---- Line edits -------------------------------------------------- */
QLineEdit {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    padding: 8px 12px;
    selection-background-color: {BLUE};
    selection-color: {CRUST};
}}
QLineEdit:focus {{
    border-color: {BLUE};
}}
QLineEdit::placeholder {{
    color: {OVERLAY0};
}}

/* ---- Spin boxes -------------------------------------------------- */
QSpinBox, QDoubleSpinBox {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    padding: 6px 10px;
    min-height: 28px;
}}
QSpinBox:focus, QDoubleSpinBox:focus {{
    border-color: {BLUE};
}}
QSpinBox::up-button, QDoubleSpinBox::up-button,
QSpinBox::down-button, QDoubleSpinBox::down-button {{
    width: 20px;
    border: none;
    background: {SURFACE1};
}}
QSpinBox::up-button:hover, QDoubleSpinBox::up-button:hover,
QSpinBox::down-button:hover, QDoubleSpinBox::down-button:hover {{
    background: {SURFACE2};
}}

/* ---- Combo boxes ------------------------------------------------- */
QComboBox {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 28px;
}}
QComboBox:focus {{
    border-color: {BLUE};
}}
QComboBox::drop-down {{
    border: none;
    width: 28px;
}}
QComboBox QAbstractItemView {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    selection-background-color: {BLUE};
    selection-color: {CRUST};
}}

/* ---- Push buttons ------------------------------------------------ */
QPushButton {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    padding: 8px 20px;
    font-weight: 600;
    min-height: 28px;
}}
QPushButton:hover {{
    background: {SURFACE1};
    border-color: {BLUE};
}}
QPushButton:pressed {{
    background: {SURFACE2};
}}
QPushButton#primaryBtn {{
    background: {BLUE};
    color: {CRUST};
    border: none;
}}
QPushButton#primaryBtn:hover {{
    background: {LAVENDER};
}}

/* ---- Tables ------------------------------------------------------ */
QTableWidget {{
    background: {MANTLE};
    alternate-background-color: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    gridline-color: {SURFACE1};
    selection-background-color: {BLUE};
    selection-color: {CRUST};
}}
QHeaderView::section {{
    background: {SURFACE0};
    color: {BLUE};
    border: none;
    border-bottom: 2px solid {BLUE};
    padding: 8px 12px;
    font-weight: 700;
    font-size: 12px;
}}
QTableWidget::item {{
    padding: 6px 12px;
}}

/* ---- Scroll bars ------------------------------------------------- */
QScrollBar:vertical {{
    background: {MANTLE};
    width: 8px;
    border-radius: 4px;
}}
QScrollBar::handle:vertical {{
    background: {SURFACE2};
    border-radius: 4px;
    min-height: 30px;
}}
QScrollBar::handle:vertical:hover {{
    background: {OVERLAY0};
}}
QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0;
}}

/* ---- Dialog button box ------------------------------------------- */
QDialogButtonBox QPushButton {{
    min-width: 90px;
}}

/* ---- Tool tips --------------------------------------------------- */
QToolTip {{
    background: {SURFACE0};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 6px;
    padding: 6px 10px;
}}

/* ---- Menu (tray) ------------------------------------------------- */
QMenu {{
    background: {MANTLE};
    color: {TEXT};
    border: 1px solid {SURFACE1};
    border-radius: 8px;
    padding: 6px;
}}
QMenu::item {{
    padding: 8px 24px 8px 12px;
    border-radius: 6px;
}}
QMenu::item:selected {{
    background: {SURFACE0};
    color: {BLUE};
}}
QMenu::separator {{
    height: 1px;
    background: {SURFACE1};
    margin: 4px 8px;
}}
QMenu::item:disabled {{
    color: {OVERLAY0};
}}

/* ---- Progress bar ------------------------------------------------ */
QProgressBar {{
    background: {SURFACE0};
    border: none;
    border-radius: 6px;
    height: 12px;
    text-align: center;
    font-size: 10px;
    color: {TEXT};
}}
QProgressBar::chunk {{
    border-radius: 6px;
}}
"""
