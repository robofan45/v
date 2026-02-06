"""Settings dialog for adjusting ResumeFlow preferences."""

import re

from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QDoubleSpinBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QLineEdit,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from .settings_manager import AppSettings

_TIME_RE = re.compile(r"^([01]\d|2[0-3]):[0-5]\d$")


class SettingsDialog(QDialog):
    """Modal dialog for editing application settings."""

    def __init__(self, settings: AppSettings, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ResumeFlow Settings")
        self.setMinimumWidth(400)
        self._settings = settings
        self._setup_ui()
        self._load_values()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        # Tracking group
        tracking_group = QGroupBox("Tracking")
        tracking_layout = QFormLayout(tracking_group)

        self._away_spin = QSpinBox()
        self._away_spin.setRange(30, 300)
        self._away_spin.setSuffix(" seconds")
        self._away_spin.setToolTip("Time away before showing resume popup (30-300s)")
        tracking_layout.addRow("Away threshold:", self._away_spin)

        self._poll_spin = QDoubleSpinBox()
        self._poll_spin.setRange(0.5, 5.0)
        self._poll_spin.setSingleStep(0.5)
        self._poll_spin.setSuffix(" seconds")
        tracking_layout.addRow("Poll interval:", self._poll_spin)

        layout.addWidget(tracking_group)

        # Popup group
        popup_group = QGroupBox("Popup")
        popup_layout = QFormLayout(popup_group)

        self._position_combo = QComboBox()
        self._position_combo.addItems(["cursor", "top-right", "bottom-right"])
        popup_layout.addRow("Position:", self._position_combo)

        self._opacity_spin = QDoubleSpinBox()
        self._opacity_spin.setRange(0.5, 1.0)
        self._opacity_spin.setSingleStep(0.05)
        popup_layout.addRow("Opacity:", self._opacity_spin)

        self._duration_spin = QSpinBox()
        self._duration_spin.setRange(0, 60)
        self._duration_spin.setSuffix(" seconds (0 = manual)")
        popup_layout.addRow("Auto-dismiss:", self._duration_spin)

        layout.addWidget(popup_group)

        # Quiet hours group
        quiet_group = QGroupBox("Quiet Hours (no popups)")
        quiet_layout = QFormLayout(quiet_group)

        self._quiet_start = QLineEdit()
        self._quiet_start.setPlaceholderText("HH:MM (e.g. 22:00)")
        quiet_layout.addRow("Start:", self._quiet_start)

        self._quiet_end = QLineEdit()
        self._quiet_end.setPlaceholderText("HH:MM (e.g. 08:00)")
        quiet_layout.addRow("End:", self._quiet_end)

        layout.addWidget(quiet_group)

        # Buttons
        buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok
            | QDialogButtonBox.StandardButton.Cancel
        )
        buttons.accepted.connect(self._validate_and_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

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
