"""Main application: wires together all ResumeFlow components.

Handles signal-based shutdown (SIGINT / SIGTERM) and ensures all
resources are cleaned up on exit.
"""

import logging
import signal
import sys

from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import QTimer

from .context_tracker import ContextTracker, ResumeInfo
from .database import SwitchLogger
from .popup import ResumePopup
from .report_dialog import ReportDialog
from .settings_dialog import SettingsDialog
from .settings_manager import SettingsManager
from .theme import APP_STYLESHEET
from .tray import TrayManager

logger = logging.getLogger(__name__)


class ResumeFlowApp:
    """Top-level application controller.

    Owns the Qt event loop, database, tracker, popup, and system tray.
    All resources are torn down in :meth:`_quit`.
    """

    def __init__(self) -> None:
        self._qt_app = QApplication(sys.argv)
        self._qt_app.setApplicationName("ResumeFlow")
        self._qt_app.setQuitOnLastWindowClosed(False)
        self._qt_app.setStyleSheet(APP_STYLESHEET)

        # Core components
        self._db = SwitchLogger()
        self._settings_mgr = SettingsManager(self._db)
        settings = self._settings_mgr.load()

        # Prune stale records on startup
        self._db.cleanup()

        # Popup widget (reused across resume events)
        self._popup = ResumePopup()
        self._popup.task_submitted.connect(self._on_task_submitted)
        self._popup.dismissed.connect(self._on_popup_dismissed)

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

        # Poll timer — drives the tracker from the main thread
        self._poll_timer = QTimer()
        self._poll_timer.timeout.connect(self._tracker.poll)
        self._poll_timer.setInterval(int(settings.poll_interval * 1000))

        self._shutting_down = False

    # -- public -----------------------------------------------------------

    def run(self) -> int:
        """Start the application and enter the Qt event loop."""
        self._install_signal_handlers()
        logger.info("ResumeFlow starting...")
        self._tray.show()
        self._tracker.start()
        self._poll_timer.start()
        return self._qt_app.exec()

    # -- signal handlers --------------------------------------------------

    def _install_signal_handlers(self) -> None:
        """Wire SIGINT / SIGTERM so the app shuts down cleanly."""
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, self._handle_signal)
        # A zero-interval timer lets the Python interpreter run between Qt
        # events so it can process the signal handler above.
        self._signal_timer = QTimer()
        self._signal_timer.start(500)
        self._signal_timer.timeout.connect(lambda: None)

    def _handle_signal(self, signum: int, _frame: object) -> None:
        logger.info("Received signal %s — shutting down", signal.Signals(signum).name)
        self._quit()

    # -- callbacks --------------------------------------------------------

    def _on_resume(self, info: ResumeInfo) -> None:
        """Called when user returns to a window after away threshold."""
        if self._settings_mgr.is_quiet_hours():
            logger.debug("Quiet hours active; suppressing popup")
            return
        settings = self._settings_mgr.current
        self._popup.show_resume(
            info,
            position=settings.popup_position,
            opacity=settings.popup_opacity,
            auto_dismiss_ms=settings.popup_duration * 1000,
        )

    def _on_task_submitted(self, task: str) -> None:
        """User entered a micro-task in the popup."""
        if task:
            self._tracker.set_micro_task(task)
            logger.info("Micro-task set: %s", task)

    def _on_popup_dismissed(self) -> None:
        """User closed the popup without entering a task."""
        logger.debug("Popup dismissed without micro-task")

    def _on_switch(self, from_title: str, to_title: str) -> None:
        """Called on every context switch."""
        logger.debug("Switch: %s -> %s", from_title, to_title)
        self._tray.refresh()

    # -- dialogs ----------------------------------------------------------

    def _show_settings(self) -> None:
        try:
            dialog = SettingsDialog(self._settings_mgr.current)
            if dialog.exec():
                new_settings = dialog.get_settings()
                self._settings_mgr.save(new_settings)
                self._tracker.update_away_threshold(new_settings.away_threshold)
                self._poll_timer.setInterval(
                    int(new_settings.poll_interval * 1000)
                )
                logger.info("Settings updated")
        except Exception:
            logger.exception("Error showing settings dialog")

    def _show_report(self) -> None:
        try:
            dialog = ReportDialog(self._db)
            dialog.exec()
        except Exception:
            logger.exception("Error showing report dialog")

    # -- shutdown ---------------------------------------------------------

    def _quit(self) -> None:
        if self._shutting_down:
            return
        self._shutting_down = True
        logger.info("ResumeFlow shutting down...")
        try:
            self._poll_timer.stop()
            self._tracker.stop()
            self._tray.cleanup()
            self._db.close()
        except Exception:
            logger.exception("Error during shutdown")
        finally:
            self._qt_app.quit()


def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    )
    try:
        app = ResumeFlowApp()
        sys.exit(app.run())
    except Exception:
        logger.exception("Fatal error in ResumeFlow")
        sys.exit(1)
