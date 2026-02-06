"""SQLite database layer for logging context switches and settings."""

import sqlite3
import os
import time
from datetime import datetime, timedelta
from typing import Optional


DB_DIR = os.path.join(os.path.expanduser("~"), ".resumeflow")
DB_PATH = os.path.join(DB_DIR, "resumeflow.db")


def get_connection(db_path: Optional[str] = None) -> sqlite3.Connection:
    path = db_path or DB_PATH
    os.makedirs(os.path.dirname(path), exist_ok=True)
    conn = sqlite3.connect(path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA synchronous=NORMAL")
    return conn


def init_db(conn: sqlite3.Connection) -> None:
    conn.executescript("""
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
    """)
    conn.commit()


class SwitchLogger:
    """Handles all database read/write operations for context switches."""

    def __init__(self, db_path: Optional[str] = None):
        self._conn = get_connection(db_path)
        init_db(self._conn)

    def close(self) -> None:
        self._conn.close()

    def log_switch(
        self,
        from_window: str,
        to_window: str,
        away_seconds: float,
        micro_task: str = "",
    ) -> int:
        cur = self._conn.execute(
            """INSERT INTO context_switches
               (timestamp, from_window, to_window, away_seconds, micro_task)
               VALUES (?, ?, ?, ?, ?)""",
            (time.time(), from_window, to_window, away_seconds, micro_task),
        )
        self._conn.commit()
        return cur.lastrowid

    def start_session(
        self, window_title: str, app_name: str = ""
    ) -> int:
        cur = self._conn.execute(
            """INSERT INTO window_sessions
               (window_title, app_name, start_time)
               VALUES (?, ?, ?)""",
            (window_title, app_name, time.time()),
        )
        self._conn.commit()
        return cur.lastrowid

    def end_session(self, session_id: int, last_context: str = "") -> None:
        self._conn.execute(
            """UPDATE window_sessions
               SET end_time = ?, last_context = ?
               WHERE id = ?""",
            (time.time(), last_context, session_id),
        )
        self._conn.commit()

    def get_last_session_for_window(self, window_title: str) -> Optional[dict]:
        row = self._conn.execute(
            """SELECT * FROM window_sessions
               WHERE window_title = ? AND end_time IS NOT NULL
               ORDER BY end_time DESC LIMIT 1""",
            (window_title,),
        ).fetchone()
        return dict(row) if row else None

    def switches_in_last_hour(self) -> int:
        one_hour_ago = time.time() - 3600
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM context_switches WHERE timestamp > ?",
            (one_hour_ago,),
        ).fetchone()
        return row["cnt"]

    def switches_today(self) -> int:
        today_start = datetime.now().replace(
            hour=0, minute=0, second=0, microsecond=0
        ).timestamp()
        row = self._conn.execute(
            "SELECT COUNT(*) as cnt FROM context_switches WHERE timestamp > ?",
            (today_start,),
        ).fetchone()
        return row["cnt"]

    def daily_score(self) -> dict:
        """Return context switch score for today.

        Score is computed as: max(100 - switches_today * 2, 0).
        Lower switch count = higher score.
        """
        total = self.switches_today()
        per_hour = self.switches_in_last_hour()
        score = max(100 - total * 2, 0)
        return {"score": score, "total_today": total, "per_hour": per_hour}

    def weekly_report(self) -> list[dict]:
        week_ago = time.time() - 7 * 86400
        rows = self._conn.execute(
            """SELECT
                 date(timestamp, 'unixepoch', 'localtime') as day,
                 COUNT(*) as switches,
                 AVG(away_seconds) as avg_away,
                 MAX(away_seconds) as max_away
               FROM context_switches
               WHERE timestamp > ?
               GROUP BY day
               ORDER BY day""",
            (week_ago,),
        ).fetchall()
        return [dict(r) for r in rows]

    def get_setting(self, key: str, default: str = "") -> str:
        row = self._conn.execute(
            "SELECT value FROM settings WHERE key = ?", (key,)
        ).fetchone()
        return row["value"] if row else default

    def set_setting(self, key: str, value: str) -> None:
        self._conn.execute(
            "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)",
            (key, value),
        )
        self._conn.commit()
