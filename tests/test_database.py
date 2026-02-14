"""Tests for the database layer."""

import pytest

from resumeflow.database import SwitchLogger


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

    def test_weekly_summary_empty(self, db):
        summary = db.weekly_summary()
        assert summary["score"] == 100
        assert summary["total_switches"] == 0

    def test_weekly_summary_with_data(self, db):
        for i in range(5):
            db.log_switch(f"W{i}", f"W{i+1}", float(i * 10))
        summary = db.weekly_summary()
        assert summary["total_switches"] == 5
        assert summary["score"] == 95
        # avg_away excludes away_seconds == 0 entries
        assert summary["avg_away"] > 0

    def test_weekly_summary_returns_defaults_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        summary = db.weekly_summary()
        assert summary == {"score": 0, "total_switches": 0, "avg_away": 0}

    def test_weekly_report_avg_excludes_zero_away(self, db):
        db.log_switch("A", "B", 0.0)  # new window, no away time
        db.log_switch("B", "A", 60.0)  # resume, 60s away
        report = db.weekly_report()
        assert len(report) == 1
        # AVG should be 60, not 30 (excludes the 0)
        assert report[0]["avg_away"] == pytest.approx(60.0)

    def test_settings_roundtrip(self, db):
        assert db.get_setting("theme") == ""
        assert db.get_setting("theme", "dark") == "dark"
        db.set_setting("theme", "light")
        assert db.get_setting("theme") == "light"
        db.set_setting("theme", "dark")
        assert db.get_setting("theme") == "dark"


class TestContextManager:
    def test_with_statement(self, tmp_path):
        path = str(tmp_path / "ctx.db")
        with SwitchLogger(path) as db:
            db.log_switch("A", "B", 1.0)
            assert db.switches_today() == 1
        # Connection closed — new one should still see data
        with SwitchLogger(path) as db2:
            assert db2.switches_today() == 1

    def test_close_is_safe_to_call_twice(self, db):
        db.close()
        db.close()  # Should not raise


class TestDatabaseErrorHandling:
    """Verify that methods return safe defaults when the DB is broken."""

    def test_log_switch_returns_none_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()  # Sabotage connection
        assert db.log_switch("A", "B", 1.0) is None

    def test_start_session_returns_none_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.start_session("A") is None

    def test_switches_today_returns_zero_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.switches_today() == 0

    def test_switches_in_last_hour_returns_zero_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.switches_in_last_hour() == 0

    def test_weekly_report_returns_empty_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.weekly_report() == []

    def test_get_setting_returns_default_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.get_setting("key", "fallback") == "fallback"

    def test_get_last_session_returns_none_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.get_last_session_for_window("A") is None

    def test_end_session_error_does_not_raise(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        db.end_session(1, "ctx")  # Should not raise

    def test_set_setting_error_does_not_raise(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        db.set_setting("key", "value")  # Should not raise

    def test_recent_switches_returns_empty_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.recent_switches() == []

    def test_cleanup_returns_zero_on_error(self, tmp_path):
        db = SwitchLogger(str(tmp_path / "err.db"))
        db._conn.close()
        assert db.cleanup() == 0


class TestRecentSwitches:
    def test_empty_db(self, db):
        assert db.recent_switches() == []

    def test_returns_recent_first(self, db):
        db.log_switch("A", "B", 10.0)
        db.log_switch("B", "C", 20.0)
        db.log_switch("C", "D", 30.0)
        result = db.recent_switches(2)
        assert len(result) == 2
        assert result[0]["from_window"] == "C"  # Most recent first
        assert result[1]["from_window"] == "B"

    def test_respects_limit(self, db):
        for i in range(10):
            db.log_switch(f"W{i}", f"W{i+1}", float(i))
        assert len(db.recent_switches(5)) == 5
        assert len(db.recent_switches(20)) == 10

    def test_has_expected_fields(self, db):
        db.log_switch("A", "B", 42.0)
        result = db.recent_switches(1)
        assert len(result) == 1
        entry = result[0]
        assert "timestamp" in entry
        assert "from_window" in entry
        assert "to_window" in entry
        assert "away_seconds" in entry
        assert entry["from_window"] == "A"
        assert entry["to_window"] == "B"
        assert entry["away_seconds"] == pytest.approx(42.0)

    def test_default_limit(self, db):
        for i in range(25):
            db.log_switch(f"W{i}", f"W{i+1}", float(i))
        result = db.recent_switches()
        assert len(result) == 20  # default limit


class TestCleanup:
    def test_cleanup_removes_old_records(self, db):
        import time
        db.log_switch("A", "B", 5.0)
        assert db.switches_today() == 1
        db._conn.execute(
            "UPDATE context_switches SET timestamp = ?",
            (time.time() - 200 * 86400,),
        )
        db._conn.commit()
        removed = db.cleanup(retention_days=90)
        assert removed >= 1

    def test_cleanup_no_old_records(self, db):
        db.log_switch("A", "B", 5.0)
        removed = db.cleanup(retention_days=90)
        assert removed == 0

    def test_daily_score_per_hour(self, db):
        db.log_switch("A", "B", 5.0)
        score = db.daily_score()
        assert score["per_hour"] >= 1
