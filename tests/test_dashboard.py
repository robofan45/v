"""Tests for the DashboardWindow."""

from resumeflow.dashboard import DashboardWindow


class TestDashboardWindow:
    def test_creates_with_empty_db(self, qapp, db):
        win = DashboardWindow(db)
        assert win.windowTitle().startswith("ResumeFlow")
        win.cleanup()
        win.close()

    def test_creates_with_data(self, qapp, db):
        for i in range(5):
            db.log_switch(f"W{i}", f"W{i+1}", float(i * 10))
        win = DashboardWindow(db)
        assert win.minimumWidth() > 0
        win.cleanup()
        win.close()

    def test_refresh_updates_without_error(self, qapp, db):
        db.log_switch("A", "B", 30.0)
        win = DashboardWindow(db)
        win.refresh()
        win.cleanup()
        win.close()

    def test_close_event_hides_instead_of_destroying(self, qapp, db):
        win = DashboardWindow(db)
        win.show()
        from PyQt6.QtGui import QCloseEvent
        event = QCloseEvent()
        win.closeEvent(event)
        assert not win.isVisible()
        assert not event.isAccepted()
        win.cleanup()

    def test_stat_cards_exist(self, qapp, db):
        win = DashboardWindow(db)
        assert win._score_card_value is not None
        assert win._switches_card_value is not None
        assert win._rate_card_value is not None
        win.cleanup()
        win.close()

    def test_table_has_correct_columns(self, qapp, db):
        win = DashboardWindow(db)
        assert win._table.columnCount() == 4
        headers = []
        for col in range(win._table.columnCount()):
            item = win._table.horizontalHeaderItem(col)
            headers.append(item.text() if item else "")
        assert "Time" in headers
        assert "Away (s)" in headers
        win.cleanup()
        win.close()

    def test_table_populated_with_switches(self, qapp, db):
        for i in range(3):
            db.log_switch(f"W{i}", f"W{i+1}", float(i * 20))
        win = DashboardWindow(db)
        assert win._table.rowCount() == 3
        win.cleanup()
        win.close()

    def test_cleanup_stops_timer(self, qapp, db):
        win = DashboardWindow(db)
        assert win._timer.isActive()
        win.cleanup()
        assert not win._timer.isActive()
        win.close()
