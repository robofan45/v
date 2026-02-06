"""System tray icon with real-time context switch count."""

from PyQt6.QtWidgets import QSystemTrayIcon, QMenu
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QFont, QAction
from PyQt6.QtCore import QTimer, QSize

from .database import SwitchLogger


def _create_tray_icon(count: int) -> QIcon:
    """Generate a 64x64 icon with the switch count rendered on it."""
    size = 64
    pixmap = QPixmap(QSize(size, size))
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setBrush(QColor("#1e1e2e"))
    painter.setPen(QColor("#89b4fa"))
    painter.drawEllipse(2, 2, size - 4, size - 4)

    # Count text
    painter.setPen(QColor("#cdd6f4"))
    font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(font)
    text = str(count) if count < 100 else "99+"
    painter.drawText(pixmap.rect(), 0x0084, text)  # AlignCenter

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """Manages the system tray icon, menu, and periodic count updates."""

    def __init__(
        self,
        db: SwitchLogger,
        on_show_settings=None,
        on_show_report=None,
        on_quit=None,
    ):
        self._db = db
        self._on_show_settings = on_show_settings
        self._on_show_report = on_show_report
        self._on_quit = on_quit

        self._tray = QSystemTrayIcon()
        self._tray.setIcon(_create_tray_icon(0))
        self._tray.setToolTip("ResumeFlow \u2014 Context Switch Tracker")

        self._menu = QMenu()
        self._score_action = QAction("Score: --/100")
        self._score_action.setEnabled(False)
        self._menu.addAction(self._score_action)

        self._switches_action = QAction("Switches today: 0")
        self._switches_action.setEnabled(False)
        self._menu.addAction(self._switches_action)

        self._menu.addSeparator()

        if on_show_report:
            report_action = QAction("Weekly Report...")
            report_action.triggered.connect(on_show_report)
            self._menu.addAction(report_action)

        if on_show_settings:
            settings_action = QAction("Settings...")
            settings_action.triggered.connect(on_show_settings)
            self._menu.addAction(settings_action)

        self._menu.addSeparator()

        if on_quit:
            quit_action = QAction("Quit")
            quit_action.triggered.connect(on_quit)
            self._menu.addAction(quit_action)

        self._tray.setContextMenu(self._menu)

        # Refresh every 10 seconds
        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)
        self._timer.start(10_000)

    def show(self) -> None:
        self._tray.show()
        self.refresh()

    def hide(self) -> None:
        self._tray.hide()

    def refresh(self) -> None:
        score_data = self._db.daily_score()
        per_hour = score_data["per_hour"]
        total = score_data["total_today"]
        score = score_data["score"]

        self._tray.setIcon(_create_tray_icon(per_hour))
        self._tray.setToolTip(
            f"ResumeFlow \u2014 Score: {score}/100 | "
            f"{per_hour}/hr | {total} today"
        )
        self._score_action.setText(f"Score: {score}/100")
        self._switches_action.setText(
            f"Switches today: {total} ({per_hour}/hr)"
        )
