"""Main application: wires together all ResumeFlow components."""

import sys
import logging

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from .database import SwitchLogger
from .context_tracker import ContextTracker, ResumeInfo
from .settings_manager import SettingsManager
from .popup import ResumePopup
from .tray import TrayManager
from .settings_dialog import SettingsDialog
from .report_dialog import ReportDialog

logger = logging.getLogger(__name__)


class ResumeFlowApp:
    """Top-level application controller."""

    def __init__(self) -> None:
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setApplicationName("ResumeFlow")
        self._qt_app.setQuitOnLastWindowClosed(False)

        # Core components
        self._db = SwitchLogger()
        self._settings_mgr = SettingsManager(self._db)
        settings = self._settings_mgr.load()

        # Popup widget
        self._popup = ResumePopup()
        self._popup.task_submitted.connect(self._on_task_submitted)

        # Context tracker
        self._tracker = ContextTracker(
            db=self._db,
            away_threshold=settings.away_threshold,
            on_resume=self._on_resume,
            on_switch=self._on_switch,
            poll_interval=settings.poll_interval,
        )

        # System tray
        self._tray = TrayManager(
            db=self._db,
            on_show_settings=self._show_settings,
            on_show_report=self._show_report,
            on_quit=self._quit,
        )

        # Poll timer
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._tracker.poll)
        self._poll_timer.setInterval(int(settings.poll_interval * 1000))

    def run(self) -> int:
        logger.info("ResumeFlow starting...")
        self._tray.show()
        self._tracker.start()
        self._poll_timer.start()
        return self._qt_app.exec()

    def _on_resume(self, info: ResumeInfo) -> None:
        """Called when user returns to a window after away threshold."""
        if self._settings_mgr.is_quiet_hours():
            logger.debug("Quiet hours active; suppressing popup")
            return
        settings = self._settings_mgr.current
        self._popup.setWindowOpacity(settings.popup_opacity)
        self._popup.show_resume(info, position=settings.popup_position)

        # Auto-dismiss if configured
        if settings.popup_duration > 0:
            QTimer.singleShot(
                settings.popup_duration * 1000, self._popup.hide
            )

    def _on_task_submitted(self, task: str) -> None:
        """User entered a micro-task in the popup."""
        if task:
            self._tracker.set_micro_task(task)
            logger.info("Micro-task set: %s", task)

    def _on_switch(self, from_title: str, to_title: str) -> None:
        """Called on every context switch."""
        logger.debug("Switch: %s -> %s", from_title, to_title)
        self._tray.refresh()

    def _show_settings(self) -> None:
        dialog = SettingsDialog(self._settings_mgr.current)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self._settings_mgr.save(new_settings)
            self._tracker.update_away_threshold(new_settings.away_threshold)
            self._poll_timer.setInterval(
                int(new_settings.poll_interval * 1000)
            )
            logger.info("Settings updated")

    def _show_report(self) -> None:
        dialog = ReportDialog(self._db)
        dialog.exec()

    def _quit(self) -> None:
        logger.info("ResumeFlow shutting down...")
        self._poll_timer.stop()
        self._tracker.stop()
        self._tray.hide()
        self._db.close()
        self._qt_app.quit()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    app = ResumeFlowApp()
    sys.exit(app.run())
