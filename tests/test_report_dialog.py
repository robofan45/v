"""Tests for the ReportDialog."""

import pytest

from resumeflow.database import SwitchLogger


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def db(tmp_path):
    logger = SwitchLogger(str(tmp_path / "report.db"))
    yield logger
    logger.close()


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
