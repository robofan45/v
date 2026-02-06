"""Tests for the ResumePopup widget."""

import pytest

from resumeflow.context_tracker import ResumeInfo


@pytest.fixture
def qapp():
    from PyQt6.QtWidgets import QApplication
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def popup(qapp):
    from resumeflow.popup import ResumePopup
    widget = ResumePopup()
    yield widget
    widget.close()


class TestResumePopup:
    def test_initial_state(self, popup):
        assert not popup.isVisible()
        assert popup.width() == 380

    def test_show_resume_populates_labels(self, popup):
        info = ResumeInfo(
            window_title="main.py - VS Code",
            app_name="Code",
            away_seconds=125,
            last_context="main.py",
        )
        popup.show_resume(info)
        assert "2m 5s" in popup._away_label.text()
        assert "main.py" in popup._context_label.text()

    def test_show_resume_falls_back_to_title(self, popup):
        info = ResumeInfo(
            window_title="Terminal",
            app_name="Terminal",
            away_seconds=60,
            last_context="",
        )
        popup.show_resume(info)
        assert "Terminal" in popup._context_label.text()

    def test_submit_hides_popup(self, popup):
        info = ResumeInfo("Win", "App", 30, "ctx")
        popup.show_resume(info)
        assert popup.isVisible()
        popup._on_submit()
        assert not popup.isVisible()

    def test_dismiss_hides_popup(self, popup):
        info = ResumeInfo("Win", "App", 30, "ctx")
        popup.show_resume(info)
        popup._on_dismiss()
        assert not popup.isVisible()

    def test_submit_emits_stripped_text(self, popup):
        received = []
        popup.task_submitted.connect(received.append)
        popup._task_input.setText("  hello  ")
        popup._on_submit()
        assert received == ["hello"]

    def test_dismiss_emits_signal(self, popup):
        received = []
        popup.dismissed.connect(lambda: received.append(True))
        popup._on_dismiss()
        assert received == [True]

    def test_position_popup_cursor_mode(self, popup):
        popup._position_popup("cursor")

    def test_position_popup_top_right(self, popup):
        popup._position_popup("top-right")

    def test_position_popup_bottom_right(self, popup):
        popup._position_popup("bottom-right")
