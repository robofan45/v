"""Main dashboard window showing focus score, recent activity, and stats."""

import logging
from datetime import datetime

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QColor, QFont
from PyQt6.QtWidgets import (
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QMainWindow,
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

_REFRESH_INTERVAL_MS = 5_000
_MAX_RECENT_SWITCHES = 20


class DashboardWindow(QMainWindow):
    """Main dashboard window for ResumeFlow.

    Displays the current focus score, today's stats, and recent context
    switches in a single window accessible from the system tray.
    """

    def __init__(self, db: SwitchLogger, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("ResumeFlow — Dashboard")
        self.setMinimumSize(620, 520)

        self._setup_ui()
        self._refresh()

        # Auto-refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(_REFRESH_INTERVAL_MS)

    def _setup_ui(self) -> None:
        central = QWidget()
        self.setCentralWidget(central)

        layout = QVBoxLayout(central)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(16)

        # ── Title ──
        title = QLabel("Dashboard")
        title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {theme.BLUE};")
        layout.addWidget(title)

        subtitle = QLabel("Your focus overview for today")
        subtitle.setFont(QFont("Segoe UI", 10))
        subtitle.setStyleSheet(f"color: {theme.SUBTEXT0};")
        layout.addWidget(subtitle)

        # ── Stat cards row ──
        card_row = QHBoxLayout()
        card_row.setSpacing(12)

        self._score_card_value = QLabel("--")
        self._score_card = self._make_stat_card(
            self._score_card_value, "Focus Score", theme.GREEN
        )
        card_row.addWidget(self._score_card)

        self._switches_card_value = QLabel("0")
        self._switches_card = self._make_stat_card(
            self._switches_card_value, "Switches Today", theme.BLUE
        )
        card_row.addWidget(self._switches_card)

        self._per_hour_card_value = QLabel("0")
        self._per_hour_card = self._make_stat_card(
            self._per_hour_card_value, "Per Hour", theme.MAUVE
        )
        card_row.addWidget(self._per_hour_card)

        layout.addLayout(card_row)

        # ── Score progress bar ──
        self._score_bar = QProgressBar()
        self._score_bar.setRange(0, 100)
        self._score_bar.setValue(0)
        self._score_bar.setFixedHeight(16)
        layout.addWidget(self._score_bar)

        # ── Recent switches table ──
        table_label = QLabel("Recent Context Switches")
        table_label.setFont(QFont("Segoe UI", 11, QFont.Weight.DemiBold))
        table_label.setStyleSheet(f"color: {theme.SUBTEXT1};")
        layout.addWidget(table_label)

        self._table = QTableWidget(0, 4)
        self._table.setHorizontalHeaderLabels(
            ["Time", "From", "To", "Away (s)"]
        )
        self._table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self._table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self._table.setAlternatingRowColors(True)
        self._table.verticalHeader().setVisible(False)
        self._table.setShowGrid(False)
        self._table.setSelectionBehavior(
            QTableWidget.SelectionBehavior.SelectRows
        )
        layout.addWidget(self._table, 1)

        self._no_data_label = QLabel("No switches recorded yet. Keep working!")
        self._no_data_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self._no_data_label.setFont(QFont("Segoe UI", 11))
        self._no_data_label.setStyleSheet(
            f"color: {theme.SUBTEXT0}; padding: 20px;"
        )
        self._no_data_label.hide()
        layout.addWidget(self._no_data_label)

    def _refresh(self) -> None:
        """Reload stats and recent switches from the database."""
        try:
            score_data = self._db.daily_score()
            score = score_data["score"]
            total = score_data["total_today"]
            per_hour = score_data["per_hour"]
            color = score_color(score)

            self._score_card_value.setText(str(score))
            self._score_card_value.setStyleSheet(f"color: {color};")
            self._switches_card_value.setText(str(total))
            self._per_hour_card_value.setText(str(per_hour))

            self._score_bar.setValue(score)
            self._score_bar.setFormat(f"  {score}/100")
            self._score_bar.setStyleSheet(f"""
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

            switches = self._db.recent_switches(_MAX_RECENT_SWITCHES)
            self._populate_table(switches)

        except Exception:
            logger.exception("Error refreshing dashboard")

    def _populate_table(self, switches: list[dict]) -> None:
        """Fill the recent-switches table."""
        self._table.setRowCount(len(switches))

        if not switches:
            self._no_data_label.show()
            self._table.hide()
            return

        self._no_data_label.hide()
        self._table.show()

        for row, entry in enumerate(switches):
            ts = entry.get("timestamp", 0)
            time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
            time_item = QTableWidgetItem(time_str)
            time_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            self._table.setItem(row, 0, time_item)

            from_item = QTableWidgetItem(
                _truncate(entry.get("from_window", ""), 40)
            )
            self._table.setItem(row, 1, from_item)

            to_item = QTableWidgetItem(
                _truncate(entry.get("to_window", ""), 40)
            )
            self._table.setItem(row, 2, to_item)

            away = entry.get("away_seconds", 0) or 0
            away_item = QTableWidgetItem(f"{away:.0f}")
            away_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
            if away >= 60:
                away_item.setForeground(QColor(theme.RED))
            elif away >= 30:
                away_item.setForeground(QColor(theme.YELLOW))
            else:
                away_item.setForeground(QColor(theme.GREEN))
            self._table.setItem(row, 3, away_item)

    def _make_stat_card(
        self, value_label: QLabel, subtitle: str, color: str
    ) -> QWidget:
        """Create a stat card with a big value label and a subtitle."""
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

        value_label.setFont(QFont("Segoe UI", 22, QFont.Weight.Bold))
        value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        value_label.setStyleSheet(f"color: {color};")
        card_layout.addWidget(value_label)

        sub = QLabel(subtitle)
        sub.setFont(QFont("Segoe UI", 9))
        sub.setAlignment(Qt.AlignmentFlag.AlignCenter)
        sub.setStyleSheet(f"color: {theme.SUBTEXT0};")
        card_layout.addWidget(sub)

        return card

    def closeEvent(self, event) -> None:  # noqa: N802
        """Hide instead of closing so it can be re-opened from tray."""
        event.ignore()
        self.hide()

    def cleanup(self) -> None:
        """Stop the refresh timer."""
        self._timer.stop()


def _truncate(text: str, max_len: int) -> str:
    """Truncate text with ellipsis if it exceeds *max_len*."""
    if len(text) <= max_len:
        return text
    return text[: max_len - 1] + "\u2026"
