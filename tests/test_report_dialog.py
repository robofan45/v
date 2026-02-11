"""Tests for the ReportDialog."""

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
