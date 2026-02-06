"""SQLite database layer for logging context switches and settings.

All public methods handle sqlite3 errors gracefully, logging failures
and returning safe defaults so the app never crashes from a DB issue.
"""

import logging
import os
import sqlite3
import time
from datetime import datetime
from typing import Optional

logger = logging.getLogger(__name__)

DB_DIR = os.path.join(os.path.expanduser("~"), ".resumeflow")
DB_PATH = os.path.join(DB_DIR, "resumeflow.db")

_SCHEMA = """
CREATE TABLE IF NOT EXISTS context_switches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp REAL NOT NULL,
    from_window TEXT,
    to_window TEXT,
    away_seconds REAL NOT NULL DEFAULT 0,
    micro_task TEXT
);

CREATE TABLE IF NOT EXISTS window_sessions (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    window_title TEXT NOT NULL,
    app_name TEXT,
    start_time REAL NOT NULL,
    end_time REAL,
    last_context TEXT
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_switches_timestamp
    ON context_switches(timestamp);
CREATE INDEX IF NOT EXISTS idx_sessions_window
    ON window_sessions(window_title);
CREATE INDEX IF NOT EXISTS idx_sessions_start
    ON window_sessions(start_time);
"""


def _connect(db_path: str) -> sqlite3.Connection:
    """Open a connection with WAL mode and row-factory enabled."""
    os.makedirs(os.path.dirname(db_path), exist_ok=True)
    conn = sqlite3.connect(db_path, timeout=5.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


class SwitchLogger:
    """Handles all database read/write operations for context switches.

    Implements the context-manager protocol so it can be used with ``with``.
    All public methods catch :class:`sqlite3.Error` and return safe defaults
    to prevent database issues from crashing the application.
    """

    def __init__(self, db_path: Optional[str] = None) -> None:
        self._path = db_path or DB_PATH
        self._conn = _connect(self._path)
        try:
            self._conn.executescript(_SCHEMA)
            self._conn.commit()
        except sqlite3.Error:
            logger.exception("Failed to initialise database schema")
            raise

    # -- context manager --------------------------------------------------

    def __enter__(self) -> "SwitchLogger":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()

    # -- lifecycle --------------------------------------------------------

    def close(self) -> None:
        try:
            self._conn.close()
        except sqlite3.Error:
            logger.exception("Error closing database connection")

    # -- writes -----------------------------------------------------------

    def log_switch(
        self,
        from_window: str,
        to_window: str,
        away_seconds: float,
        micro_task: str = "",
    ) -> Optional[int]:
        try:
            cur = self._conn.execute(
                """INSERT INTO context_switches
                   (timestamp, from_window, to_window, away_seconds, micro_task)
                   VALUES (?, ?, ?, ?, ?)""",
                (time.time(), from_window, to_window, away_seconds, micro_task),
            )
            self._conn.commit()
            return cur.lastrowid
        except sqlite3.Error:
            logger.exception("Failed to log context switch")
            return None

    def start_session(self, window_title: str, app_name: str = "") -> Optional[int]:
        try:
            cur = self._conn.execute(
                """INSERT INTO window_sessions
                   (window_title, app_name, start_time)
                   VALUES (?, ?, ?)""",
                (window_title, app_name, time.time()),
            )
            self._conn.commit()
            return cur.lastrowid
        except sqlite3.Error:
            logger.exception("Failed to start window session")
            return None

    def end_session(self, session_id: int, last_context: str = "") -> None:
        try:
            self._conn.execute(
                """UPDATE window_sessions
                   SET end_time = ?, last_context = ?
                   WHERE id = ?""",
                (time.time(), last_context, session_id),
            )
            self._conn.commit()
        except sqlite3.Error:
            logger.exception("Failed to end window session %d", session_id)

    # -- reads ------------------------------------------------------------

    def get_last_session_for_window(self, window_title: str) -> Optional[dict]:
        try:
            row = self._conn.execute(
                """SELECT * FROM window_sessions
                   WHERE window_title = ? AND end_time IS NOT NULL
                   ORDER BY end_time DESC LIMIT 1""",
                (window_title,),
            ).fetchone()
            return dict(row) if row else None
        except sqlite3.Error:
            logger.exception("Failed to query last session for window")
            return None

    def switches_in_last_hour(self) -> int:
        try:
            one_hour_ago = time.time() - 3600
            row = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM context_switches WHERE timestamp > ?",
                (one_hour_ago,),
            ).fetchone()
            return row["cnt"] if row else 0
        except sqlite3.Error:
            logger.exception("Failed to count switches in last hour")
            return 0

    def switches_today(self) -> int:
        try:
            today_start = datetime.now().replace(
                hour=0, minute=0, second=0, microsecond=0
            ).timestamp()
            row = self._conn.execute(
                "SELECT COUNT(*) as cnt FROM context_switches WHERE timestamp > ?",
                (today_start,),
            ).fetchone()
            return row["cnt"] if row else 0
        except sqlite3.Error:
            logger.exception("Failed to count today's switches")
            return 0

    def daily_score(self) -> dict:
        """Return context switch score for today.

        Score: ``max(100 - switches_today * 2, 0)``.
        Lower switch count = higher score.
        """
        total = self.switches_today()
        per_hour = self.switches_in_last_hour()
        score = max(100 - total * 2, 0)
        return {"score": score, "total_today": total, "per_hour": per_hour}

    def weekly_report(self) -> list[dict]:
        try:
            week_ago = time.time() - 7 * 86400
            rows = self._conn.execute(
                """SELECT
                     date(timestamp, 'unixepoch', 'localtime') as day,
                     COUNT(*) as switches,
                     COALESCE(AVG(away_seconds), 0) as avg_away,
                     COALESCE(MAX(away_seconds), 0) as max_away
                   FROM context_switches
                   WHERE timestamp > ?
                   GROUP BY day
                   ORDER BY day""",
                (week_ago,),
            ).fetchall()
            return [dict(r) for r in rows]
        except sqlite3.Error:
            logger.exception("Failed to generate weekly report")
            return []

    # -- settings ---------------------------------------------------------

    def get_setting(self, key: str, default: str = "") -> str:
        try:
            row = self._conn.execute(
                "SELECT value FROM settings WHERE key = ?", (key,)
            ).fetchone()
            return row["value"] if row else default
        except sqlite3.Error:
            logger.exception("Failed to read setting '%s'", key)
            return default

    def set_setting(self, key: str, value: str) -> None:
        try:
            self._conn.execute(
                "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
                (key, value),
            )
            self._conn.commit()
        except sqlite3.Error:
            logger.exception("Failed to write setting '%s'", key)
