"""Tests for the tray icon rendering logic (non-GUI parts)."""

from unittest.mock import MagicMock

from resumeflow.tray import _create_tray_icon, _ICON_SIZE, TrayManager


class TestCreateTrayIcon:
    def test_icon_not_null(self, qapp):
        icon = _create_tray_icon(0)
        assert not icon.isNull()

    def test_icon_with_count(self, qapp):
        icon = _create_tray_icon(42)
        assert not icon.isNull()

    def test_icon_caps_at_99_plus(self, qapp):
        icon = _create_tray_icon(150)
        assert not icon.isNull()

    def test_icon_size(self, qapp):
        icon = _create_tray_icon(5)
        sizes = icon.availableSizes()
        assert len(sizes) > 0
        assert sizes[0].width() == _ICON_SIZE
        assert sizes[0].height() == _ICON_SIZE

    def test_icon_with_low_score(self, qapp):
        icon = _create_tray_icon(10, score=20)
        assert not icon.isNull()

    def test_icon_with_mid_score(self, qapp):
        icon = _create_tray_icon(10, score=50)
        assert not icon.isNull()

    def test_icon_with_high_score(self, qapp):
        icon = _create_tray_icon(10, score=90)
        assert not icon.isNull()


class TestTrayManager:
    def test_construction(self, qapp, db):
        tray = TrayManager(db=db)
        assert tray._tray is not None
        tray.cleanup()

    def test_menu_has_score_action(self, qapp, db):
        tray = TrayManager(db=db)
        assert tray._score_action is not None
        assert "Score" in tray._score_action.text()
        tray.cleanup()

    def test_menu_has_switches_action(self, qapp, db):
        tray = TrayManager(db=db)
        assert tray._switches_action is not None
        assert "Switches" in tray._switches_action.text()
        tray.cleanup()

    def test_dashboard_action_created(self, qapp, db):
        callback = MagicMock()
        tray = TrayManager(db=db, on_show_dashboard=callback)
        assert tray._dashboard_action is not None
        assert tray._dashboard_action.text() == "Dashboard..."
        tray.cleanup()

    def test_report_action_created(self, qapp, db):
        callback = MagicMock()
        tray = TrayManager(db=db, on_show_report=callback)
        assert tray._report_action is not None
        assert tray._report_action.text() == "Weekly Report..."
        tray.cleanup()

    def test_settings_action_created(self, qapp, db):
        callback = MagicMock()
        tray = TrayManager(db=db, on_show_settings=callback)
        assert tray._settings_action is not None
        assert tray._settings_action.text() == "Settings..."
        tray.cleanup()

    def test_quit_action_created(self, qapp, db):
        callback = MagicMock()
        tray = TrayManager(db=db, on_quit=callback)
        assert tray._quit_action is not None
        assert tray._quit_action.text() == "Quit"
        tray.cleanup()

    def test_refresh_updates_tooltip(self, qapp, db):
        tray = TrayManager(db=db)
        tray.refresh()
        tooltip = tray._tray.toolTip()
        assert "Score" in tooltip
        tray.cleanup()

    def test_cleanup_stops_timer(self, qapp, db):
        tray = TrayManager(db=db)
        tray.show()
        assert tray._timer.isActive()
        tray.cleanup()
        assert not tray._timer.isActive()
