"""Core context tracking engine.

Monitors active window changes, detects away periods,
and triggers resume popups when the user returns to a
previously visited window after the configured threshold.
"""

import collections
import logging
import time
from dataclasses import dataclass
from typing import Callable, Optional

from .database import SwitchLogger
from .window_monitor import get_active_window

logger = logging.getLogger(__name__)

# Keep at most this many window history entries to bound memory.
_MAX_HISTORY = 500


@dataclass
class WindowState:
    """Snapshot of the currently focused window."""

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
    db:
        Database logger instance.
    away_threshold:
        Seconds of absence before showing a resume popup (default 30).
    on_resume:
        Called with *ResumeInfo* when user returns after threshold.
    on_switch:
        Called on every context switch with *(from_title, to_title)*.
    poll_interval:
        Seconds between active window checks (default 1.0).
    """

    def __init__(
        self,
        db: SwitchLogger,
        away_threshold: float = 30.0,
        on_resume: Optional[Callable[[ResumeInfo], None]] = None,
        on_switch: Optional[Callable[[str, str], None]] = None,
        poll_interval: float = 1.0,
    ) -> None:
        self.db = db
        self.away_threshold = away_threshold
        self.on_resume = on_resume
        self.on_switch = on_switch
        self.poll_interval = poll_interval

        self._current: Optional[WindowState] = None
        # Bounded LRU dict: title -> (left_at, last_context)
        self._window_history: collections.OrderedDict[
            str, tuple[float, str]
        ] = collections.OrderedDict()
        self._running = False
        self._empty_polls: int = 0
        self._warned_no_detection = False

    @property
    def running(self) -> bool:
        return self._running

    def start(self) -> None:
        self._running = True
        logger.info("Context tracker started (threshold=%ss)", self.away_threshold)

    def stop(self) -> None:
        self._running = False
        if self._current and self._current.session_id is not None:
            self.db.end_session(
                self._current.session_id, self._current.last_context
            )
        logger.info("Context tracker stopped")

    def poll(self) -> None:
        """Check the active window once. Call this from a QTimer."""
        if not self._running:
            return

        try:
            title, app_name = get_active_window()
        except Exception:
            logger.debug("Window detection failed during poll", exc_info=True)
            return

        if not title:
            self._empty_polls += 1
            if self._empty_polls >= 30 and not self._warned_no_detection:
                logger.warning(
                    "Window detection returned empty %d times in a row. "
                    "Check that pygetwindow (Windows) or xdotool (Linux) "
                    "is installed.",
                    self._empty_polls,
                )
                self._warned_no_detection = True
            return

        self._empty_polls = 0
        now = time.time()

        # Same window — no switch
        if self._current and self._current.title == title:
            return

        # Window changed
        prev = self._current

        # Close previous session
        if prev:
            if prev.session_id is not None:
                self.db.end_session(prev.session_id, prev.last_context)
            self._window_history[prev.title] = (now, prev.last_context)
            # Move to end (most-recently used) and enforce size cap.
            self._window_history.move_to_end(prev.title)
            while len(self._window_history) > _MAX_HISTORY:
                self._window_history.popitem(last=False)

        # Check if we're returning to a known window
        away: float = 0
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
                try:
                    self.on_resume(info)
                except Exception:
                    logger.exception("Error in on_resume callback")

        # Log switch
        if prev:
            self.db.log_switch(
                from_window=prev.title,
                to_window=title,
                away_seconds=away,
            )
            if self.on_switch:
                try:
                    self.on_switch(prev.title, title)
                except Exception:
                    logger.exception("Error in on_switch callback")

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
        """Store a micro-task note for the current window.

        Persists to the DB so the context survives a crash.
        """
        if self._current:
            self._current.last_context = task
            if self._current.session_id is not None:
                self.db.end_session(self._current.session_id, task)
                self._current.session_id = self.db.start_session(
                    self._current.title, self._current.app_name
                )

    def update_away_threshold(self, seconds: float) -> None:
        self.away_threshold = seconds
        logger.info("Away threshold updated to %ss", seconds)


def _extract_context(window_title: str) -> str:
    """Extract a useful context hint from a window title.

    Tries to pull file names, document titles, or URLs from
    common title bar formats like::

        main.py - MyProject - VS Code
        Report.docx - Microsoft Word
        GitHub - Pull Request #42 - Firefox
    """
    if not window_title:
        return ""
    parts = [p.strip() for p in window_title.split(" - ")]
    return parts[0] if parts else window_title
