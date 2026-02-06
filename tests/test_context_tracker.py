"""Tests for the context tracker engine."""

import time
from unittest.mock import MagicMock, patch

import pytest

from resumeflow.context_tracker import (
    ContextTracker,
    ResumeInfo,
    _MAX_HISTORY,
    _extract_context,
)
from resumeflow.database import SwitchLogger


@pytest.fixture
def db(tmp_path):
    logger = SwitchLogger(str(tmp_path / "test.db"))
    yield logger
    logger.close()


class TestExtractContext:
    def test_simple_title(self):
        assert _extract_context("main.py - VS Code") == "main.py"

    def test_multi_dash(self):
        assert _extract_context("Report.docx - Microsoft Word") == "Report.docx"

    def test_no_dash(self):
        assert _extract_context("Terminal") == "Terminal"

    def test_empty(self):
        assert _extract_context("") == ""


class TestResumeInfo:
    def test_away_seconds(self):
        info = ResumeInfo("Win", "App", 45, "ctx")
        assert info.away_display == "45s"

    def test_away_minutes(self):
        info = ResumeInfo("Win", "App", 125, "ctx")
        assert info.away_display == "2m 5s"

    def test_away_hours(self):
        info = ResumeInfo("Win", "App", 3725, "ctx")
        assert info.away_display == "1h 2m"


class TestContextTracker:
    @patch("resumeflow.context_tracker.get_active_window")
    def test_no_switch_on_same_window(self, mock_get, db):
        mock_get.return_value = ("Window A", "App A")
        on_switch = MagicMock()
        tracker = ContextTracker(db, on_switch=on_switch)
        tracker.start()

        tracker.poll()
        tracker.poll()
        tracker.poll()

        on_switch.assert_not_called()

    @patch("resumeflow.context_tracker.get_active_window")
    def test_switch_detected(self, mock_get, db):
        on_switch = MagicMock()
        tracker = ContextTracker(db, on_switch=on_switch)
        tracker.start()

        mock_get.return_value = ("Window A", "App A")
        tracker.poll()

        mock_get.return_value = ("Window B", "App B")
        tracker.poll()

        on_switch.assert_called_once_with("Window A", "Window B")

    @patch("resumeflow.context_tracker.get_active_window")
    def test_resume_triggered_after_threshold(self, mock_get, db):
        on_resume = MagicMock()
        tracker = ContextTracker(
            db, away_threshold=1.0, on_resume=on_resume
        )
        tracker.start()

        mock_get.return_value = ("Window A", "App A")
        tracker.poll()

        mock_get.return_value = ("Window B", "App B")
        tracker.poll()

        time.sleep(1.1)

        mock_get.return_value = ("Window A", "App A")
        tracker.poll()

        on_resume.assert_called_once()
        info = on_resume.call_args[0][0]
        assert isinstance(info, ResumeInfo)
        assert info.window_title == "Window A"
        assert info.away_seconds >= 1.0

    @patch("resumeflow.context_tracker.get_active_window")
    def test_no_resume_under_threshold(self, mock_get, db):
        on_resume = MagicMock()
        tracker = ContextTracker(
            db, away_threshold=30.0, on_resume=on_resume
        )
        tracker.start()

        mock_get.return_value = ("Window A", "App A")
        tracker.poll()
        mock_get.return_value = ("Window B", "App B")
        tracker.poll()
        mock_get.return_value = ("Window A", "App A")
        tracker.poll()

        on_resume.assert_not_called()

    @patch("resumeflow.context_tracker.get_active_window")
    def test_empty_title_ignored(self, mock_get, db):
        tracker = ContextTracker(db)
        tracker.start()
        mock_get.return_value = ("", "")
        tracker.poll()
        assert tracker._current is None

    @patch("resumeflow.context_tracker.get_active_window")
    def test_set_micro_task(self, mock_get, db):
        tracker = ContextTracker(db)
        tracker.start()
        mock_get.return_value = ("Window A", "App A")
        tracker.poll()
        tracker.set_micro_task("fix the login bug")
        assert tracker._current.last_context == "fix the login bug"

    @patch("resumeflow.context_tracker.get_active_window")
    def test_stop_ends_session(self, mock_get, db):
        tracker = ContextTracker(db)
        tracker.start()
        mock_get.return_value = ("Window A", "App A")
        tracker.poll()
        assert tracker.running
        tracker.stop()
        assert not tracker.running

    @patch("resumeflow.context_tracker.get_active_window")
    def test_poll_does_nothing_when_not_running(self, mock_get, db):
        tracker = ContextTracker(db)
        # Not started
        tracker.poll()
        mock_get.assert_not_called()

    @patch("resumeflow.context_tracker.get_active_window")
    def test_window_detection_error_handled(self, mock_get, db):
        mock_get.side_effect = RuntimeError("xdotool died")
        tracker = ContextTracker(db)
        tracker.start()
        tracker.poll()  # Should not raise
        assert tracker._current is None

    @patch("resumeflow.context_tracker.get_active_window")
    def test_on_resume_callback_error_handled(self, mock_get, db):
        on_resume = MagicMock(side_effect=ValueError("popup crashed"))
        tracker = ContextTracker(
            db, away_threshold=0.0, on_resume=on_resume
        )
        tracker.start()

        mock_get.return_value = ("A", "App")
        tracker.poll()
        mock_get.return_value = ("B", "App")
        tracker.poll()
        mock_get.return_value = ("A", "App")
        tracker.poll()  # Should not propagate ValueError

    @patch("resumeflow.context_tracker.get_active_window")
    def test_on_switch_callback_error_handled(self, mock_get, db):
        on_switch = MagicMock(side_effect=TypeError("bad callback"))
        tracker = ContextTracker(db, on_switch=on_switch)
        tracker.start()

        mock_get.return_value = ("A", "App")
        tracker.poll()
        mock_get.return_value = ("B", "App")
        tracker.poll()  # Should not propagate TypeError


class TestWindowHistoryBound:
    @patch("resumeflow.context_tracker.get_active_window")
    def test_history_does_not_exceed_max(self, mock_get, db):
        tracker = ContextTracker(db)
        tracker.start()

        for i in range(_MAX_HISTORY + 50):
            mock_get.return_value = (f"Window-{i}", "App")
            tracker.poll()

        assert len(tracker._window_history) <= _MAX_HISTORY

    @patch("resumeflow.context_tracker.get_active_window")
    def test_lru_eviction_removes_oldest(self, mock_get, db):
        tracker = ContextTracker(db)
        tracker.start()

        # Need _MAX_HISTORY + 2 unique windows: the last is _current (not in
        # history), so the history holds _MAX_HISTORY + 1 before eviction
        # kicks in and removes the oldest entry.
        for i in range(_MAX_HISTORY + 2):
            mock_get.return_value = (f"Window-{i}", "App")
            tracker.poll()

        assert "Window-0" not in tracker._window_history
        # The most recent is _current, previous one should be in history
        assert f"Window-{_MAX_HISTORY}" in tracker._window_history
