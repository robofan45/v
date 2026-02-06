"""Non-intrusive floating resume popup widget."""

import logging

from PyQt6.QtCore import QPoint, Qt, pyqtSignal
from PyQt6.QtGui import QCursor, QFont
from PyQt6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from .context_tracker import ResumeInfo

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
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, False)
        self.setFixedWidth(380)

        self._setup_ui()
        self._setup_style()

    # -- UI setup ---------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()
        self._icon_label = QLabel("\u23f0")
        self._icon_label.setFont(QFont("Segoe UI Emoji", 14))
        header.addWidget(self._icon_label)

        self._title_label = QLabel("Welcome back!")
        self._title_label.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        header.addWidget(self._title_label, 1)

        close_btn = QPushButton("\u2715")
        close_btn.setFixedSize(24, 24)
        close_btn.setObjectName("closeBtn")
        close_btn.clicked.connect(self._on_dismiss)
        header.addWidget(close_btn)

        layout.addLayout(header)

        # Away info
        self._away_label = QLabel()
        self._away_label.setWordWrap(True)
        self._away_label.setFont(QFont("Segoe UI", 9))
        layout.addWidget(self._away_label)

        # Context info
        self._context_label = QLabel()
        self._context_label.setWordWrap(True)
        self._context_label.setFont(QFont("Segoe UI", 9))
        self._context_label.setObjectName("contextLabel")
        layout.addWidget(self._context_label)

        # Micro-task input
        task_label = QLabel("Ready to Resume \u2014 what's your next micro-task?")
        task_label.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        layout.addWidget(task_label)

        input_row = QHBoxLayout()
        self._task_input = QLineEdit()
        self._task_input.setPlaceholderText("e.g. Fix the login bug on line 42...")
        self._task_input.returnPressed.connect(self._on_submit)
        input_row.addWidget(self._task_input, 1)

        go_btn = QPushButton("Go \u2192")
        go_btn.setObjectName("goBtn")
        go_btn.clicked.connect(self._on_submit)
        input_row.addWidget(go_btn)

        layout.addLayout(input_row)

    def _setup_style(self) -> None:
        self.setStyleSheet("""
            ResumePopup {
                background-color: #1e1e2e;
                border: 1px solid #45475a;
                border-radius: 12px;
            }
            QLabel {
                color: #cdd6f4;
                background: transparent;
            }
            QLabel#contextLabel {
                color: #a6e3a1;
                padding: 4px 8px;
                background: #1a1a2e;
                border-radius: 6px;
            }
            QLineEdit {
                background: #313244;
                color: #cdd6f4;
                border: 1px solid #45475a;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #89b4fa;
            }
            QPushButton#goBtn {
                background: #89b4fa;
                color: #1e1e2e;
                border: none;
                border-radius: 6px;
                padding: 6px 16px;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#goBtn:hover {
                background: #74c7ec;
            }
            QPushButton#closeBtn {
                background: transparent;
                color: #6c7086;
                border: none;
                font-size: 14px;
            }
            QPushButton#closeBtn:hover {
                color: #f38ba8;
            }
        """)

    # -- public API -------------------------------------------------------

    def show_resume(self, info: ResumeInfo, position: str = "cursor") -> None:
        """Populate and display the popup for a resume event."""
        self._away_label.setText(f"You were away for {info.away_display}.")
        context_text = info.last_context or info.window_title
        self._context_label.setText(f"You were working on: {context_text}")
        self._task_input.clear()
        self._task_input.setFocus()

        self.adjustSize()
        self._position_popup(position)
        self.show()
        self.raise_()
        self.activateWindow()
        logger.debug("Resume popup shown (away %s)", info.away_display)

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

    # -- slots ------------------------------------------------------------

    def _on_submit(self) -> None:
        text = self._task_input.text().strip()
        self.task_submitted.emit(text)
        self.hide()

    def _on_dismiss(self) -> None:
        self.dismissed.emit()
        self.hide()
