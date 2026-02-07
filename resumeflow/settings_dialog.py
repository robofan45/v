"""Settings dialog for adjusting ResumeFlow preferences with polished UI."""

import re

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .settings_manager import AppSettings
from . import theme

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class SettingsDialog(QDialog):
    """Modal dialog for editing application settings."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ResumeFlow Settings")
        self.setMinimumWidth(460)
        self._settings = settings
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("Settings")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.BLUE};")
        layout.addWidget(title)

        subtitle = QLabel("Customise how ResumeFlow behaves")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {theme.SUBTEXT0};")
        layout.addWidget(subtitle)

        # ── Tracking group ──
        tracking_group = QGroupBox("Tracking")
        tracking_layout = QFormLayout(tracking_group)
        tracking_layout.setSpacing(12)
        tracking_layout.setContentsMargins(16, 20, 16, 12)

        self._away_spin = QSpinBox()
        self._away_spin.setRange(30, 300)
        self._away_spin.setSuffix(" seconds")
        self._away_spin.setToolTip("Time away before showing resume popup (30-300s)")
        tracking_layout.addRow(self._make_label("Away threshold"), self._away_spin)

        self._poll_spin = QDoubleSpinBox()
        self._poll_spin.setRange(0.5, 5.0)
        self._poll_spin.setSingleStep(0.5)
        self._poll_spin.setSuffix(" seconds")
        self._poll_spin.setToolTip("How often to check the active window")
        tracking_layout.addRow(self._make_label("Poll interval"), self._poll_spin)

        layout.addWidget(tracking_group)

        # ── Popup group ──
        popup_group = QGroupBox("Popup")
        popup_layout = QFormLayout(popup_group)
        popup_layout.setSpacing(12)
        popup_layout.setContentsMargins(16, 20, 16, 12)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["cursor", "top-right", "bottom-right"])
        popup_layout.addRow(self._make_label("Position"), self._position_combo)

        self._opacity_spin = QDoubleSpinBox()
        self._opacity_spin.setRange(0.5, 1.0)
        self._opacity_spin.setSingleStep(0.05)
        popup_layout.addRow(self._make_label("Opacity"), self._opacity_spin)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 60)
        self._duration_spin.setSuffix(" seconds (0 = manual)")
        self._duration_spin.setToolTip("Auto-dismiss popup after N seconds")
        popup_layout.addRow(self._make_label("Auto-dismiss"), self._duration_spin)

        layout.addWidget(popup_group)

        # ── Quiet hours group ──
        quiet_group = QGroupBox("Quiet Hours")
        quiet_layout = QFormLayout(quiet_group)
        quiet_layout.setSpacing(12)
        quiet_layout.setContentsMargins(16, 20, 16, 12)

        quiet_desc = QLabel("Suppress popups during these hours")
        quiet_desc.setFont(QFont("Segoe UI", 9))
        quiet_desc.setStyleSheet(f"color: {theme.SUBTEXT0};")
        quiet_layout.addRow(quiet_desc)

        self._quiet_start = QLineEdit()
        self._quiet_start.setPlaceholderText("HH:MM (e.g. 22:00)")
        quiet_layout.addRow(self._make_label("Start"), self._quiet_start)

        self._quiet_end = QLineEdit()
        self._quiet_end.setPlaceholderText("HH:MM (e.g. 08:00)")
        quiet_layout.addRow(self._make_label("End"), self._quiet_end)

        layout.addWidget(quiet_group)

        layout.addStretch()

        # ── Buttons ──
        btn_row = QHBoxLayout()
        btn_row.addStretch()

        cancel_btn = QPushButton("Cancel")
        cancel_btn.clicked.connect(self.reject)
        btn_row.addWidget(cancel_btn)

        save_btn = QPushButton("Save")
        save_btn.setObjectName("primaryBtn")
        save_btn.clicked.connect(self._validate_and_accept)
        btn_row.addWidget(save_btn)

        layout.addLayout(btn_row)

    def _make_label(self, text: str) -> QLabel:
        """Create a styled form row label."""
        label = QLabel(text)
        label.setFont(QFont("Segoe UI", 10))
        label.setStyleSheet(f"color: {theme.SUBTEXT1};")
        return label

    def _load_values(self) -> None:
        s = self._settings
        self._away_spin.setValue(s.away_threshold)
        self._poll_spin.setValue(s.poll_interval)
        idx = self._position_combo.findText(s.popup_position)
        if idx >= 0:
            self._position_combo.setCurrentIndex(idx)
        self._opacity_spin.setValue(s.popup_opacity)
        self._duration_spin.setValue(s.popup_duration)
        self._quiet_start.setText(s.quiet_hours_start)
        self._quiet_end.setText(s.quiet_hours_end)

    def _validate_and_accept(self) -> None:
        """Validate quiet-hours format before accepting."""
        start = self._quiet_start.text().strip()
        end = self._quiet_end.text().strip()
        # Both empty is fine (quiet hours disabled).
        if start or end:
            if not (_TIME_RE.match(start) and _TIME_RE.match(end)):
                QMessageBox.warning(
                    self,
                    "Invalid time",
                    "Quiet hours must be in HH:MM format (e.g. 22:00).",
                )
                return
        self.accept()

    def get_settings(self) -> AppSettings:
        return AppSettings(
            away_threshold=self._away_spin.value(),
            poll_interval=self._poll_spin.value(),
            popup_position=self._position_combo.currentText(),
            popup_opacity=self._opacity_spin.value(),
            popup_duration=self._duration_spin.value(),
            quiet_hours_start=self._quiet_start.text().strip(),
            quiet_hours_end=self._quiet_end.text().strip(),
        )
