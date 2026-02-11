"""Shared pytest fixtures for all ResumeFlow tests."""

import pytest

from resumeflow.database import SwitchLogger


@pytest.fixture
def qapp():
    """Ensure a QApplication exists for widget / pixmap tests."""
    from PyQt6.QtWidgets import QApplication

    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    yield app


@pytest.fixture
def db(tmp_path):
    """Provide a fresh SwitchLogger backed by a temporary database."""
    logger = SwitchLogger(str(tmp_path / "test.db"))
    yield logger
    logger.close()
