"""Weekly report dialog showing context switch statistics."""

from PyQt6.QtWidgets import (
    QDialog, QVBoxLayout, QLabel, QTableWidget, QTableWidgetItem,
    QHeaderView, QDialogButtonBox,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QFont

from .database import SwitchLogger


class ReportDialog(QDialog):
    def __init__(self, db: SwitchLogger, parent=None):
        super().__init__(parent)
        self.setWindowTitle("ResumeFlow \u2014 Weekly Report")
        self.setMinimumSize(500, 350)
        self._db = db
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)

        title = QLabel("Context Switch Report (Last 7 Days)")
        title.setFont(QFont("Segoe UI", 13, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title)

        # Daily score
        score_data = self._db.daily_score()
        score_label = QLabel(
            f"Today's Score: {score_data['score']}/100  |  "
            f"Switches today: {score_data['total_today']}  |  "
            f"Last hour: {score_data['per_hour']}"
        )
        score_label.setFont(QFont("Segoe UI", 10))
        score_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(score_label)

        # Table
        report = self._db.weekly_report()
        table = QTableWidget(len(report), 4)
        table.setHorizontalHeaderLabels(
            ["Date", "Switches", "Avg Away (s)", "Max Away (s)"]
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)

        for row, entry in enumerate(report):
            table.setItem(row, 0, QTableWidgetItem(entry["day"]))
            table.setItem(row, 1, QTableWidgetItem(str(entry["switches"])))
            avg = f"{entry['avg_away']:.0f}" if entry["avg_away"] else "0"
            table.setItem(row, 2, QTableWidgetItem(avg))
            max_away = f"{entry['max_away']:.0f}" if entry["max_away"] else "0"
            table.setItem(row, 3, QTableWidgetItem(max_away))

        layout.addWidget(table)

        if not report:
            no_data = QLabel("No data yet. Keep using ResumeFlow!")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setFont(QFont("Segoe UI", 10))
            layout.addWidget(no_data)

        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        layout.addWidget(buttons)
