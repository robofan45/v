"""Core context tracking engine.

Monitors active window changes, detects away periods,
and triggers resume popups when the user returns to a
previously visited window after the configured threshold.
"""

import time
import logging
from dataclasses import dataclass, field
from typing import Optional, Callable

from .window_monitor import get_active_window
from .database import SwitchLogger

logger = logging.getLogger(__name__)


@dataclass
class WindowState:
    title: str
    app_name: str
    entered_at: float
    session_id: Optional[int] = None
    last_context: str = ""


@dataclass
class ResumeInfo:
    """Data passed to the popup when user returns to a window."""
    window_title: str
    app_name: str
    away_seconds: float
    last_context: str

    @property
    def away_display(self) -> str:
        secs = int(self.away_seconds)
        if secs < 60:
            return f"{secs}s"
        mins = secs // 60
        remaining = secs % 60
        if mins < 60:
            return f"{mins}m {remaining}s"
        hours = mins // 60
        remaining_mins = mins % 60
        return f"{hours}h {remaining_mins}m"


class ContextTracker:
    """Tracks window focus changes and detects context switches.

    Parameters
    ----------
    db : SwitchLogger
        Database logger instance.
    away_threshold : float
        Seconds of absence before showing a resume popup (default 30).
    on_resume : callable, optional
        Called with ResumeInfo when user returns after threshold.
    on_switch : callable, optional
        Called on every context switch with (from_title, to_title).
    poll_interval : float
        Seconds between active window checks (default 1.0).
    """

    def __init__(
        self,
        db: SwitchLogger,
        away_threshold: float = 30.0,
        on_resume: Optional[Callable[[ResumeInfo], None]] = None,
        on_switch: Optional[Callable[[str, str], None]] = None,
        poll_interval: float = 1.0,
    ):
        self.db = db
        self.away_threshold = away_threshold
        self.on_resume = on_resume
        self.on_switch = on_switch
        self.poll_interval = poll_interval

        self._current: Optional[WindowState] = None
        # Track the last time each window was active: title -> (left_at, last_context)
        self._window_history: dict[str, tuple[float, str]] = {}
        self._running = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True

    def stop(self) -> None:
        self._running = False
        if self._current and self._current.session_id:
            self.db.end_session(
                self._current.session_id, self._current.last_context
            )

    def poll(self) -> None:
        """Check the active window once. Call this from a QTimer."""
        if not self._running:
            return

        title, app_name = get_active_window()
        if not title:
            return

        now = time.time()

        # Same window — no switch
        if self._current and self._current.title == title:
            return

        # Window changed
        prev = self._current

        # Close previous session
        if prev:
            if prev.session_id:
                self.db.end_session(prev.session_id, prev.last_context)
            self._window_history[prev.title] = (now, prev.last_context)

        # Check if we're returning to a known window
        if title in self._window_history:
            left_at, last_ctx = self._window_history[title]
            away = now - left_at
            if away >= self.away_threshold and self.on_resume:
                info = ResumeInfo(
                    window_title=title,
                    app_name=app_name,
                    away_seconds=away,
                    last_context=last_ctx or _extract_context(title),
                )
                self.on_resume(info)
        else:
            away = 0

        # Log switch
        if prev:
            self.db.log_switch(
                from_window=prev.title,
                to_window=title,
                away_seconds=away,
            )
            if self.on_switch:
                self.on_switch(prev.title, title)

        # Start new session
        session_id = self.db.start_session(title, app_name)
        self._current = WindowState(
            title=title,
            app_name=app_name,
            entered_at=now,
            session_id=session_id,
            last_context=_extract_context(title),
        )

    def set_micro_task(self, task: str) -> None:
        """Store a micro-task note for the current window."""
        if self._current:
            self._current.last_context = task

    def update_away_threshold(self, seconds: float) -> None:
        self.away_threshold = seconds


def _extract_context(window_title: str) -> str:
    """Extract a useful context hint from a window title.

    Tries to pull file names, document titles, or URLs from
    common title bar formats like:
      "main.py - MyProject - VS Code"
      "Report.docx - Microsoft Word"
      "GitHub - Pull Request #42 - Firefox"
    """
    if not window_title:
        return ""
    parts = [p.strip() for p in window_title.split(" - ")]
    # First part is usually the most specific (file name, doc title)
    return parts[0] if parts else window_title
