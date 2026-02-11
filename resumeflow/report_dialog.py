"""Weekly report dialog with visual score gauge and styled table."""

import logging

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QProgressBar,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

from .database import SwitchLogger
from . import theme
from .theme import score_color

logger = logging.getLogger(__name__)


class ReportDialog(QDialog):
    """Modal dialog displaying a weekly context-switch report."""

    def __init__(self, db: SwitchLogger, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setWindowTitle("ResumeFlow \u2014 Weekly Report")
        self.setMinimumSize(580, 460)
        self._db = db
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("Weekly Focus Report")
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setStyleSheet(f"color: {theme.BLUE};")
        layout.addWidget(title)

        subtitle = QLabel("Your context switching stats for the last 7 days")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setAlignment(Qt.AlignmentFlag.AlignCenter)
        subtitle.setStyleSheet(f"color: {theme.SUBTEXT0};")
        layout.addWidget(subtitle)

        # ── Score card row (weekly aggregate) ──
        try:
            weekly = self._db.weekly_summary()
        except Exception:
            logger.exception("Failed to load weekly summary for report")
            weekly = {"score": 0, "total_switches": 0, "avg_away": 0}

        score = weekly["score"]
        color = score_color(score)

        card_row = QHBoxLayout()
        card_row.setSpacing(12)

        # Score card
        score_card = self._make_stat_card(
            f"{score}", "Weekly Score", color
        )
        card_row.addWidget(score_card)

        # Total switches card
        switches_card = self._make_stat_card(
            str(weekly["total_switches"]), "Total Switches", theme.BLUE
        )
        card_row.addWidget(switches_card)

        # Avg away card
        avg_away = weekly["avg_away"]
        avg_str = f"{avg_away:.0f}s" if avg_away else "—"
        avg_card = self._make_stat_card(
            avg_str, "Avg Away", theme.MAUVE
        )
        card_row.addWidget(avg_card)

        layout.addLayout(card_row)

        # ── Score progress bar ──
        bar = QProgressBar()
        bar.setRange(0, 100)
        bar.setValue(score)
        bar.setFormat(f"  {score}/100")
        bar.setFixedHeight(16)
        bar.setStyleSheet(f"""
            QProgressBar {{
                background: {theme.SURFACE0};
                border: none;
                border-radius: 8px;
                text-align: left;
                font-size: 10px;
                font-weight: bold;
                color: {theme.TEXT};
            }}
            QProgressBar::chunk {{
                background: {color};
                border-radius: 8px;
            }}
        """)
        layout.addWidget(bar)

        # ── Table ──
        try:
            report = self._db.weekly_report()
        except Exception:
            logger.exception("Failed to load weekly report data")
            report = []

        table_label = QLabel("Daily Breakdown")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        table_label.setStyleSheet(f"color: {theme.SUBTEXT1};")
        layout.addWidget(table_label)

        table = QTableWidget(len(report), 4)
        table.setHorizontalHeaderLabels(
            ["Date", "Switches", "Avg Away (s)", "Max Away (s)"]
        )
        table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        table.setAlternatingRowColors(True)
        table.verticalHeader().setVisible(False)
        table.setShowGrid(False)
        table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)

        for row, entry in enumerate(report):
            date_item = QTableWidgetItem(str(entry.get("day", "")))
            date_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            table.setItem(row, 0, date_item)

            sw_item = QTableWidgetItem(str(entry.get("switches", 0)))
            sw_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            sw_count = entry.get("switches", 0)
            if sw_count > 30:
                sw_item.setForeground(QColor(theme.RED))
            elif sw_count > 15:
                sw_item.setForeground(QColor(theme.YELLOW))
            else:
                sw_item.setForeground(QColor(theme.GREEN))
            table.setItem(row, 1, sw_item)

            avg = entry.get("avg_away", 0) or 0
            avg_item = QTableWidgetItem(f"{avg:.0f}")
            avg_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            table.setItem(row, 2, avg_item)

            max_away = entry.get("max_away", 0) or 0
            max_item = QTableWidgetItem(f"{max_away:.0f}")
            max_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            table.setItem(row, 3, max_item)

        layout.addWidget(table, 1)

        if not report:
            no_data = QLabel("No data yet. Keep using ResumeFlow!")
            no_data.setAlignment(Qt.AlignmentFlag.AlignCenter)
            no_data.setFont(QFont("Segoe UI", 11))
            no_data.setStyleSheet(f"color: {theme.SUBTEXT0}; padding: 20px;")
            layout.addWidget(no_data)

        # ── Close button ──
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok)
        buttons.accepted.connect(self.accept)
        ok_btn = buttons.button(QDialogButtonBox.StandardButton.Ok)
        if ok_btn:
            ok_btn.setText("Close")
            ok_btn.setObjectName("primaryBtn")
        layout.addWidget(buttons)

    def _make_stat_card(self, value: str, label: str, color: str) -> QWidget:
        """Create a small stat card widget with a big value and a subtitle."""
        card = QWidget()
        card.setObjectName("statCard")
        card.setStyleSheet(f"""
            QWidget#statCard {{
                background: {theme.MANTLE};
                border: 1px solid {theme.SURFACE1};
                border-radius: 10px;
                padding: 12px;
            }}
        """)
        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(16, 12, 16, 12)
        card_layout.setSpacing(2)
        card_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        val_label = QLabel(value)
        val_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        val_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        val_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(val_label)

        sub_label = QLabel(label)
        sub_label.setFont(QFont("Segoe UI", 9))
        sub_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub_label.setStyleSheet(f"color: {theme.SUBTEXT0};")
        card_layout.addWidget(sub_label)

        return card
