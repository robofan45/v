"""Tests for the dashboard window."""

import time

import pytest

from resumeflow.dashboard import DashboardWindow, _truncate
from resumeflow.database import SwitchLogger


@pytest.fixture
def dashboard(qapp, db):
    """Create a DashboardWindow backed by a temporary database."""
    win = DashboardWindow(db)
    yield win
    win.cleanup()
    win.close()


class TestDashboardWindow:
    def test_creates_without_error(self, dashboard):
        assert dashboard is not None

    def test_window_title(self, dashboard):
        assert "Dashboard" in dashboard.windowTitle()

    def test_minimum_size(self, dashboard):
        assert dashboard.minimumWidth() >= 620
        assert dashboard.minimumHeight() >= 520

    def test_stat_cards_exist(self, dashboard):
        assert dashboard._score_card_value is not None
        assert dashboard._switches_card_value is not None
        assert dashboard._per_hour_card_value is not None

    def test_initial_score_card(self, dashboard):
        # Score defaults to 100 with no switches
        text = dashboard._score_card_value.text()
        assert text == "100"

    def test_table_has_correct_headers(self, dashboard):
        table = dashboard._table
        assert table.columnCount() == 4
        headers = [
            table.horizontalHeaderItem(i).text() for i in range(4)
        ]
        assert headers == ["Time", "From", "To", "Away (s)"]

    def test_table_empty_with_no_data(self, dashboard):
        assert dashboard._table.rowCount() == 0

    def test_no_data_label_shown_when_empty(self, dashboard):
        # The no-data label should not be hidden when there are no switches.
        # Note: isVisible() requires the parent to be shown, so we check
        # that the label is not explicitly hidden.
        assert not dashboard._no_data_label.isHidden()

    def test_refresh_with_data(self, dashboard, db):
        db.log_switch("Window A", "Window B", 10.0)
        db.log_switch("Window B", "Window C", 45.0)
        dashboard._refresh()

        assert dashboard._table.rowCount() == 2
        assert not dashboard._no_data_label.isVisible()

    def test_score_updates_after_switches(self, dashboard, db):
        for i in range(5):
            db.log_switch(f"Win {i}", f"Win {i + 1}", 5.0)
        dashboard._refresh()

        score_text = dashboard._score_card_value.text()
        # 100 - 5*2 = 90
        assert score_text == "90"

    def test_close_event_hides_window(self, qapp, dashboard):
        dashboard.show()
        dashboard.close()
        assert not dashboard.isVisible()

    def test_cleanup_stops_timer(self, dashboard):
        assert dashboard._timer.isActive()
        dashboard.cleanup()
        assert not dashboard._timer.isActive()


class TestTruncate:
    def test_short_string_unchanged(self):
        assert _truncate("hello", 10) == "hello"

    def test_exact_length_unchanged(self):
        assert _truncate("hello", 5) == "hello"

    def test_long_string_truncated(self):
        result = _truncate("hello world", 6)
        assert len(result) == 6
        assert result.endswith("\u2026")

    def test_empty_string(self):
        assert _truncate("", 10) == ""


class TestRecentSwitches:
    def test_recent_switches_empty(self, db):
        assert db.recent_switches() == []

    def test_recent_switches_returns_data(self, db):
        db.log_switch("A", "B", 5.0)
        db.log_switch("B", "C", 10.0)
        result = db.recent_switches()
        assert len(result) == 2
        # Newest first
        assert result[0]["from_window"] == "B"
        assert result[1]["from_window"] == "A"

    def test_recent_switches_respects_limit(self, db):
        for i in range(10):
            db.log_switch(f"W{i}", f"W{i + 1}", 1.0)
        result = db.recent_switches(limit=3)
        assert len(result) == 3

    def test_recent_switches_returns_empty_on_error(self, db):
        db._conn.close()
        assert db.recent_switches() == []
