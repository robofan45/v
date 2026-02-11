"""Tests for the tray icon rendering logic (non-GUI parts)."""

from resumeflow.tray import _create_tray_icon, _ICON_SIZE


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
