"""Tests for the database layer."""

import os
import tempfile
import time

import pytest

from resumeflow.database import SwitchLogger, get_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def db(db_path):
    logger = SwitchLogger(db_path)
    yield logger
    logger.close()


class TestSwitchLogger:
    def test_log_switch(self, db):
        row_id = db.log_switch("Window A", "Window B", 45.0, "fix bug")
        assert row_id == 1

    def test_switches_today(self, db):
        assert db.switches_today() == 0
        db.log_switch("A", "B", 10.0)
        db.log_switch("B", "C", 20.0)
        assert db.switches_today() == 2

    def test_switches_in_last_hour(self, db):
        assert db.switches_in_last_hour() == 0
        db.log_switch("A", "B", 5.0)
        assert db.switches_in_last_hour() == 1

    def test_session_lifecycle(self, db):
        sid = db.start_session("VS Code - main.py", "Code")
        assert sid >= 1
        db.end_session(sid, "editing main.py")

        last = db.get_last_session_for_window("VS Code - main.py")
        assert last is not None
        assert last["last_context"] == "editing main.py"
        assert last["end_time"] is not None

    def test_get_last_session_none(self, db):
        result = db.get_last_session_for_window("nonexistent")
        assert result is None

    def test_daily_score(self, db):
        score = db.daily_score()
        assert score["score"] == 100
        assert score["total_today"] == 0

        for i in range(10):
            db.log_switch(f"W{i}", f"W{i+1}", 5.0)
        score = db.daily_score()
        assert score["score"] == 80
        assert score["total_today"] == 10

    def test_daily_score_floor(self, db):
        for i in range(60):
            db.log_switch(f"W{i}", f"W{i+1}", 1.0)
        score = db.daily_score()
        assert score["score"] == 0

    def test_weekly_report_empty(self, db):
        report = db.weekly_report()
        assert report == []

    def test_weekly_report_has_data(self, db):
        db.log_switch("A", "B", 30.0)
        db.log_switch("B", "C", 60.0)
        report = db.weekly_report()
        assert len(report) == 1
        assert report[0]["switches"] == 2

    def test_settings_roundtrip(self, db):
        assert db.get_setting("theme") == ""
        assert db.get_setting("theme", "dark") == "dark"
        db.set_setting("theme", "light")
        assert db.get_setting("theme") == "light"
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"
