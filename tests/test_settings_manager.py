"""Tests for the settings manager."""

import json
from datetime import datetime
from unittest.mock import patch

import pytest

from resumeflow.database import SwitchLogger
from resumeflow.settings_manager import SettingsManager, AppSettings


@pytest.fixture
def db(tmp_path):
    logger = SwitchLogger(str(tmp_path / "test.db"))
    yield logger
    logger.close()


class TestSettingsManager:
    def test_default_settings(self, db):
        mgr = SettingsManager(db)
        s = mgr.load()
        assert s.away_threshold == 30
        assert s.popup_position == "cursor"
        assert s.quiet_hours_start == ""

    def test_save_and_load(self, db):
        mgr = SettingsManager(db)
        custom = AppSettings(
            away_threshold=120,
            popup_position="top-right",
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        )
        mgr.save(custom)

        mgr2 = SettingsManager(db)
        loaded = mgr2.load()
        assert loaded.away_threshold == 120
        assert loaded.popup_position == "top-right"
        assert loaded.quiet_hours_start == "22:00"

    def test_current_property(self, db):
        mgr = SettingsManager(db)
        s = mgr.current
        assert isinstance(s, AppSettings)

    @patch("resumeflow.settings_manager.datetime")
    def test_quiet_hours_active(self, mock_dt, db):
        mock_now = datetime(2025, 1, 1, 23, 30)
        mock_dt.now.return_value = mock_now

        mgr = SettingsManager(db)
        mgr.save(AppSettings(
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        ))
        assert mgr.is_quiet_hours() is True

    @patch("resumeflow.settings_manager.datetime")
    def test_quiet_hours_inactive(self, mock_dt, db):
        mock_now = datetime(2025, 1, 1, 12, 0)
        mock_dt.now.return_value = mock_now

        mgr = SettingsManager(db)
        mgr.save(AppSettings(
            quiet_hours_start="22:00",
            quiet_hours_end="08:00",
        ))
        assert mgr.is_quiet_hours() is False

    def test_quiet_hours_empty(self, db):
        mgr = SettingsManager(db)
        mgr.load()
        assert mgr.is_quiet_hours() is False

    def test_quiet_hours_invalid_format(self, db):
        mgr = SettingsManager(db)
        mgr.save(AppSettings(
            quiet_hours_start="not-a-time",
            quiet_hours_end="also-bad",
        ))
        assert mgr.is_quiet_hours() is False

    def test_load_ignores_unknown_fields(self, db):
        """Settings saved with extra keys from a newer version load fine."""
        data = {"away_threshold": 60, "future_field": True}
        db.set_setting("app_settings", json.dumps(data))
        mgr = SettingsManager(db)
        s = mgr.load()
        assert s.away_threshold == 60
        assert not hasattr(s, "future_field")

    def test_load_corrupt_json_falls_back(self, db):
        db.set_setting("app_settings", "NOT-JSON{{{{")
        mgr = SettingsManager(db)
        s = mgr.load()
        assert s == AppSettings()
