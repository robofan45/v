"""Tests for the SettingsDialog."""

import pytest

from resumeflow.settings_manager import AppSettings


class TestSettingsDialog:
    def test_loads_defaults(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        result = dialog.get_settings()
        assert result.away_threshold == 30
        assert result.popup_position == "cursor"
        dialog.close()

    def test_loads_custom(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        custom = AppSettings(
            away_threshold=120,
            popup_position="top-right",
            poll_interval=2.0,
        )
        dialog = SettingsDialog(custom)
        result = dialog.get_settings()
        assert result.away_threshold == 120
        assert result.popup_position == "top-right"
        assert result.poll_interval == 2.0
        dialog.close()

    def test_roundtrip_preserves_values(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        original = AppSettings(
            away_threshold=60,
            popup_position="bottom-right",
            popup_opacity=0.8,
            popup_duration=10,
            quiet_hours_start="22:00",
            quiet_hours_end="06:00",
            poll_interval=1.5,
        )
        dialog = SettingsDialog(original)
        result = dialog.get_settings()
        assert result.away_threshold == original.away_threshold
        assert result.popup_position == original.popup_position
        assert result.popup_opacity == pytest.approx(original.popup_opacity, abs=0.01)
        assert result.popup_duration == original.popup_duration
        assert result.quiet_hours_start == original.quiet_hours_start
        assert result.quiet_hours_end == original.quiet_hours_end
        dialog.close()

    def test_away_threshold_range(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        assert dialog._away_spin.minimum() == 30
        assert dialog._away_spin.maximum() == 300
        dialog.close()

    def test_poll_interval_range(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        assert dialog._poll_spin.minimum() == 0.5
        assert dialog._poll_spin.maximum() == 5.0
        dialog.close()

    def test_opacity_range(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        assert dialog._opacity_spin.minimum() == 0.5
        assert dialog._opacity_spin.maximum() == 1.0
        dialog.close()

    def test_auto_dismiss_range(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        assert dialog._duration_spin.minimum() == 0
        assert dialog._duration_spin.maximum() == 60
        dialog.close()

    def test_position_options(self, qapp):
        from resumeflow.settings_dialog import SettingsDialog
        dialog = SettingsDialog(AppSettings())
        options = [dialog._position_combo.itemText(i)
                   for i in range(dialog._position_combo.count())]
        assert "cursor" in options
        assert "top-right" in options
        assert "bottom-right" in options
        dialog.close()
