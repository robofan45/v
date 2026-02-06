"""System tray icon with real-time context switch count."""

import logging
from typing import Callable, Optional

from PyQt6.QtCore import QSize, QTimer, Qt
from PyQt6.QtGui import QAction, QColor, QFont, QIcon, QPainter, QPixmap
from PyQt6.QtWidgets import QMenu, QSystemTrayIcon

from .database import SwitchLogger

logger = logging.getLogger(__name__)

_ICON_SIZE = 64


def _create_tray_icon(count: int) -> QIcon:
    """Generate a 64x64 icon with the switch count rendered on it."""
    pixmap = QPixmap(QSize(_ICON_SIZE, _ICON_SIZE))
    pixmap.fill(QColor(0, 0, 0, 0))

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # Background circle
    painter.setBrush(QColor("#1e1e2e"))
    painter.setPen(QColor("#89b4fa"))
    painter.drawEllipse(2, 2, _ICON_SIZE - 4, _ICON_SIZE - 4)

    # Count text
    painter.setPen(QColor("#cdd6f4"))
    font = QFont("Segoe UI", 22, QFont.Weight.Bold)
    painter.setFont(font)
    text = str(count) if count < 100 else "99+"
    painter.drawText(pixmap.rect(), int(Qt.AlignmentFlag.AlignCenter), text)

    painter.end()
    return QIcon(pixmap)


class TrayManager:
    """Manages the system tray icon, menu, and periodic count updates.

    Call :meth:`cleanup` to stop the internal refresh timer and hide the
    tray icon before the application exits.
    """

    def __init__(
        self,
        db: SwitchLogger,
        on_show_settings: Optional[Callable[[], None]] = None,
        on_show_report: Optional[Callable[[], None]] = None,
        on_quit: Optional[Callable[[], None]] = None,
    ) -> None:
        self._db = db

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

        # Periodic refresh (every 10 s)
        self._timer = QTimer()
        self._timer.timeout.connect(self.refresh)

    # -- public -----------------------------------------------------------

    def show(self) -> None:
        self._tray.show()
        self._timer.start(10_000)
        self.refresh()

    def hide(self) -> None:
        self._tray.hide()

    def cleanup(self) -> None:
        """Stop the refresh timer and hide the tray icon."""
        self._timer.stop()
        self._tray.hide()
        logger.debug("Tray manager cleaned up")

    def refresh(self) -> None:
        """Re-read switch counts from the database and update the UI."""
        try:
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
        except Exception:
            logger.exception("Error refreshing tray icon")
