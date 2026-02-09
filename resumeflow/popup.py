"""Non-intrusive floating resume popup widget with polished UI."""

import logging

from PyQt6.QtCore import QPoint, QPropertyAnimation, QEasingCurve, QTimer, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QCursor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QGraphicsDropShadowEffect,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .context_tracker import ResumeInfo
from . import theme

logger = logging.getLogger(__name__)


class ResumePopup(QWidget):
    """Small floating popup shown when returning to a window after away time.

    Displays:
    - How long the user was away
    - What they were last working on
    - A micro-task text field for the next action

    Signals
    -------
    task_submitted(str)
        Emitted with the micro-task text when user clicks *Go* or presses Enter.
    dismissed()
        Emitted when popup is closed without a task.
    """

    task_submitted = pyqtSignal(str)
    dismissed = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setFixedWidth(420)
        self._target_opacity: float = 0.95
        self._auto_dismiss_timer: QTimer | None = None

        self._setup_ui()
        self._setup_style()

    # -- UI setup ---------------------------------------------------------

    def _setup_ui(self) -> None:
        # Outer wrapper so the drop shadow has room to render
        outer = QVBoxLayout(self)
        outer.setContentsMargins(12, 12, 12, 12)

        self._card = QWidget()
        self._card.setObjectName("popupCard")
        card_layout = QVBoxLayout(self._card)
        card_layout.setContentsMargins(20, 16, 20, 16)
        card_layout.setSpacing(12)

        # Drop shadow
        shadow = QGraphicsDropShadowEffect(self._card)
        shadow.setBlurRadius(30)
        shadow.setOffset(0, 4)
        shadow.setColor(QColor(theme.CRUST))
        self._card.setGraphicsEffect(shadow)

        # ── Header row ──
        header = QHBoxLayout()
        header.setSpacing(10)

        self._icon_label = QLabel("\u23f0")
        self._icon_label.setFont(QFont("Segoe UI Emoji", 18))
        self._icon_label.setFixedWidth(32)
        header.addWidget(self._icon_label)

        header_text = QVBoxLayout()
        header_text.setSpacing(0)
        self._title_label = QLabel("Welcome back!")
        self._title_label.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        self._title_label.setObjectName("popupTitle")
        header_text.addWidget(self._title_label)

        self._away_label = QLabel()
        self._away_label.setFont(QFont("Segoe UI", 10))
        self._away_label.setObjectName("awayLabel")
        header_text.addWidget(self._away_label)

        header.addLayout(header_text, 1)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(28, 28)
        close_btn.setObjectName("closeBtn")
        close_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        close_btn.clicked.connect(self._on_dismiss)
        header.addWidget(close_btn)

        card_layout.addLayout(header)

        # ── Divider ──
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setObjectName("divider")
        card_layout.addWidget(divider)

        # ── Context card ──
        self._context_label = QLabel()
        self._context_label.setWordWrap(True)
        self._context_label.setFont(QFont("Segoe UI", 10))
        self._context_label.setObjectName("contextLabel")
        card_layout.addWidget(self._context_label)

        # ── Micro-task section ──
        task_label = QLabel("\u270f  What's your next micro-task?")
        task_label.setFont(QFont("Segoe UI", 10, QFont.Weight.DemiBold))
        task_label.setObjectName("taskPromptLabel")
        card_layout.addWidget(task_label)

        input_row = QHBoxLayout()
        input_row.setSpacing(8)
        self._task_input = QLineEdit()
        self._task_input.setPlaceholderText("e.g. Fix the login bug on line 42...")
        self._task_input.setMinimumHeight(36)
        self._task_input.returnPressed.connect(self._on_submit)
        input_row.addWidget(self._task_input, 1)

        go_btn = QPushButton("Go  \u2192")
        go_btn.setObjectName("goBtn")
        go_btn.setMinimumHeight(36)
        go_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        go_btn.clicked.connect(self._on_submit)
        input_row.addWidget(go_btn)

        card_layout.addLayout(input_row)

        outer.addWidget(self._card)

    def _setup_style(self) -> None:
        self.setStyleSheet(f"""
            QWidget#popupCard {{
                background-color: {theme.BASE};
                border: 1px solid {theme.SURFACE1};
                border-radius: 14px;
            }}
            QLabel {{
                color: {theme.TEXT};
                background: transparent;
            }}
            QLabel#popupTitle {{
                color: {theme.BLUE};
                font-size: 14px;
            }}
            QLabel#awayLabel {{
                color: {theme.SUBTEXT0};
                font-size: 11px;
            }}
            QLabel#contextLabel {{
                color: {theme.GREEN};
                padding: 10px 14px;
                background: {theme.MANTLE};
                border-radius: 8px;
                border-left: 3px solid {theme.GREEN};
                font-size: 12px;
            }}
            QLabel#taskPromptLabel {{
                color: {theme.SUBTEXT1};
            }}
            QWidget#divider {{
                background-color: {theme.SURFACE1};
            }}
            QLineEdit {{
                background: {theme.SURFACE0};
                color: {theme.TEXT};
                border: 1px solid {theme.SURFACE1};
                border-radius: 8px;
                padding: 8px 12px;
                font-size: 13px;
            }}
            QLineEdit:focus {{
                border-color: {theme.BLUE};
            }}
            QPushButton#goBtn {{
                background: {theme.BLUE};
                color: {theme.CRUST};
                border: none;
                border-radius: 8px;
                padding: 8px 22px;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#goBtn:hover {{
                background: {theme.LAVENDER};
            }}
            QPushButton#goBtn:pressed {{
                background: {theme.MAUVE};
            }}
            QPushButton#closeBtn {{
                background: transparent;
                color: {theme.OVERLAY0};
                border: none;
                border-radius: 14px;
                font-size: 14px;
            }}
            QPushButton#closeBtn:hover {{
                color: {theme.RED};
                background: {theme.SURFACE0};
            }}
        """)

    # -- public API -------------------------------------------------------

    def show_resume(
        self,
        info: ResumeInfo,
        position: str = "cursor",
        opacity: float = 0.95,
        auto_dismiss_ms: int = 0,
    ) -> None:
        """Populate and display the popup for a resume event.

        Parameters
        ----------
        opacity:
            Target window opacity after fade-in (0.0-1.0).
        auto_dismiss_ms:
            Auto-hide after this many milliseconds.  0 = manual dismiss.
        """
        # Cancel any pending auto-dismiss from a previous popup.
        self._cancel_auto_dismiss()

        self._target_opacity = max(0.1, min(opacity, 1.0))

        self._away_label.setText(f"You were away for {info.away_display}")
        context_text = info.last_context or info.window_title
        self._context_label.setText(f"\U0001f4cc  Last working on: {context_text}")
        self._task_input.clear()
        self._task_input.setFocus()

        self.adjustSize()
        self._position_popup(position)
        self.show()
        self.raise_()
        self.activateWindow()

        # Fade-in animation
        self._fade_in()

        # Schedule auto-dismiss (after fade-in completes)
        if auto_dismiss_ms > 0:
            self._auto_dismiss_timer = QTimer(self)
            self._auto_dismiss_timer.setSingleShot(True)
            self._auto_dismiss_timer.timeout.connect(self._on_dismiss)
            self._auto_dismiss_timer.start(auto_dismiss_ms + 200)

        logger.debug("Resume popup shown (away %s)", info.away_display)

    # -- animation --------------------------------------------------------

    def _fade_in(self) -> None:
        self.setWindowOpacity(0.0)
        self._anim = QPropertyAnimation(self, b"windowOpacity")
        self._anim.setDuration(200)
        self._anim.setStartValue(0.0)
        self._anim.setEndValue(self._target_opacity)
        self._anim.setEasingCurve(QEasingCurve.Type.OutCubic)
        self._anim.start()

    # -- positioning ------------------------------------------------------

    def _position_popup(self, mode: str) -> None:
        screen = QApplication.primaryScreen()
        cursor_pos = QCursor.pos()

        if mode == "top-right" and screen:
            geo = screen.availableGeometry()
            self.move(geo.right() - self.width() - 20, geo.top() + 20)
            return

        if mode == "bottom-right" and screen:
            geo = screen.availableGeometry()
            self.move(
                geo.right() - self.width() - 20,
                geo.bottom() - self.height() - 20,
            )
            return

        # Default: near cursor
        x = cursor_pos.x() + 20
        y = cursor_pos.y() + 20

        if screen:
            geo = screen.availableGeometry()
            if x + self.width() > geo.right():
                x = cursor_pos.x() - self.width() - 10
            if y + self.height() > geo.bottom():
                y = cursor_pos.y() - self.height() - 10
            x = max(x, geo.left())
            y = max(y, geo.top())

        self.move(QPoint(x, y))

    # -- auto-dismiss management ------------------------------------------

    def _cancel_auto_dismiss(self) -> None:
        """Stop and discard any pending auto-dismiss timer."""
        if self._auto_dismiss_timer is not None:
            self._auto_dismiss_timer.stop()
            self._auto_dismiss_timer.deleteLater()
            self._auto_dismiss_timer = None

    # -- slots ------------------------------------------------------------

    def _on_submit(self) -> None:
        text = self._task_input.text().strip()
        if not text:
            # Don't emit empty tasks — just dismiss instead
            self._on_dismiss()
            return
        self._cancel_auto_dismiss()
        self.task_submitted.emit(text)
        self.hide()

    def _on_dismiss(self) -> None:
        self._cancel_auto_dismiss()
        self.dismissed.emit()
        self.hide()
