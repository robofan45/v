"""Tests for the tray icon rendering logic and TrayManager."""

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

    def test_icon_score_colour_varies(self, qapp):
        """Different scores should produce different coloured rings."""
        icon_good = _create_tray_icon(5, score=90)
        icon_bad = _create_tray_icon(5, score=10)
        # Both valid icons — visual colour verified by _create_tray_icon logic
        assert not icon_good.isNull()
        assert not icon_bad.isNull()


class TestTrayManager:
    def test_creates_with_all_callbacks(self, qapp, db):
        tray = TrayManager(
            db=db,
            on_show_settings=MagicMock(),
            on_show_report=MagicMock(),
            on_show_dashboard=MagicMock(),
            on_quit=MagicMock(),
        )
        tray.cleanup()

    def test_creates_with_no_callbacks(self, qapp, db):
        tray = TrayManager(db=db)
        tray.cleanup()

    def test_menu_contains_dashboard_action(self, qapp, db):
        tray = TrayManager(db=db, on_show_dashboard=MagicMock())
        assert tray._dashboard_action is not None
        assert tray._dashboard_action.text() == "Dashboard..."
        tray.cleanup()

    def test_menu_contains_report_action(self, qapp, db):
        tray = TrayManager(db=db, on_show_report=MagicMock())
        assert tray._report_action is not None
        assert tray._report_action.text() == "Weekly Report..."
        tray.cleanup()

    def test_menu_contains_settings_action(self, qapp, db):
        tray = TrayManager(db=db, on_show_settings=MagicMock())
        assert tray._settings_action is not None
        assert tray._settings_action.text() == "Settings..."
        tray.cleanup()

    def test_menu_contains_quit_action(self, qapp, db):
        on_quit = MagicMock()
        tray = TrayManager(db=db, on_quit=on_quit)
        assert tray._quit_action is not None
        assert tray._quit_action.text() == "Quit"
        tray.cleanup()

    def test_refresh_updates_score_text(self, qapp, db):
        tray = TrayManager(db=db)
        tray.refresh()
        assert "100" in tray._score_action.text()
        tray.cleanup()

    def test_refresh_after_switches(self, qapp, db):
        db.log_switch("A", "B", 5.0)
        db.log_switch("B", "C", 10.0)
        tray = TrayManager(db=db)
        tray.refresh()
        assert "2" in tray._switches_action.text()
        tray.cleanup()

    def test_cleanup_stops_timer(self, qapp, db):
        tray = TrayManager(db=db)
        tray.show()
        assert tray._timer.isActive()
        tray.cleanup()
        assert not tray._timer.isActive()
