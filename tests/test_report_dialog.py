"""Tests for the ReportDialog."""

import pytest

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

    def test_minimum_size(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        assert dialog.minimumWidth() >= 580
        assert dialog.minimumHeight() >= 460
        dialog.close()

    def test_title_label_contains_weekly(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QLabel
        labels = dialog.findChildren(QLabel)
        title_texts = [l.text() for l in labels]
        assert any("Weekly" in t for t in title_texts)
        dialog.close()

    def test_table_has_correct_headers(self, qapp, db):
        db.log_switch("A", "B", 10.0)
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QTableWidget
        tables = dialog.findChildren(QTableWidget)
        assert len(tables) == 1
        table = tables[0]
        assert table.columnCount() == 4
        headers = [table.horizontalHeaderItem(i).text() for i in range(4)]
        assert "Date" in headers
        assert "Switches" in headers
        dialog.close()

    def test_table_populated_with_data(self, qapp, db):
        db.log_switch("A", "B", 10.0)
        db.log_switch("B", "C", 20.0)
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QTableWidget
        table = dialog.findChildren(QTableWidget)[0]
        assert table.rowCount() >= 1
        dialog.close()

    def test_no_data_label_shown_when_empty(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QLabel
        labels = dialog.findChildren(QLabel)
        label_texts = [l.text() for l in labels]
        assert any("No data" in t for t in label_texts)
        dialog.close()

    def test_progress_bar_exists(self, qapp, db):
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QProgressBar
        bars = dialog.findChildren(QProgressBar)
        assert len(bars) == 1
        assert bars[0].maximum() == 100
        dialog.close()

    def test_score_reflects_data(self, qapp, db):
        for i in range(10):
            db.log_switch(f"W{i}", f"W{i+1}", 5.0)
        from resumeflow.report_dialog import ReportDialog
        dialog = ReportDialog(db)
        from PyQt6.QtWidgets import QProgressBar
        bar = dialog.findChildren(QProgressBar)[0]
        # weekly score = max(100 - 10, 0) = 90
        assert bar.value() == 90
        dialog.close()
