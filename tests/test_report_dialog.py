"""Tests for the ReportDialog."""

from PyQt6.QtWidgets import QProgressBar, QTableWidget, QLabel

from resumeflow.database import SwitchLogger


class TestReportDialog:
    def test_creates_with_empty_db(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        assert dialog.windowTitle().startswith("ResumeFlow")
        dialog.close()

    def test_creates_with_data(self, qapp, db):
        for i in range(5):
            db.log_switch(f"W{i}", f"W{i+1}", float(i * 10))
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        assert dialog.minimumWidth() > 0
        dialog.close()

    def test_table_has_correct_headers(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        tables = dialog.findChildren(QTableWidget)
        assert len(tables) == 1
        table = tables[0]
        headers = []
        for col in range(table.columnCount()):
            item = table.horizontalHeaderItem(col)
            headers.append(item.text() if item else "")
        assert "Date" in headers
        assert "Switches" in headers
        assert "Avg Away (s)" in headers
        assert "Max Away (s)" in headers
        dialog.close()

    def test_table_populated_with_data(self, qapp, db):
        db.log_switch("A", "B", 30.0)
        db.log_switch("B", "C", 60.0)
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        tables = dialog.findChildren(QTableWidget)
        assert tables[0].rowCount() >= 1
        dialog.close()

    def test_progress_bar_exists(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        bars = dialog.findChildren(QProgressBar)
        assert len(bars) == 1
        dialog.close()

    def test_progress_bar_range(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        bar = dialog.findChildren(QProgressBar)[0]
        assert bar.minimum() == 0
        assert bar.maximum() == 100
        dialog.close()

    def test_score_value_in_progress_bar(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        bar = dialog.findChildren(QProgressBar)[0]
        assert 0 <= bar.value() <= 100
        dialog.close()

    def test_no_data_label_shown(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        labels = dialog.findChildren(QLabel)
        label_texts = [l.text() for l in labels]
        assert any("No data" in t for t in label_texts)
        dialog.close()
