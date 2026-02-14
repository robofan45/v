"""Dashboard window showing live focus stats and recent context switches."""

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


class DashboardWindow(QMainWindow):
    """Main dashboard window with live stats and recent switches table.

    Hides on close instead of destroying so it can be reopened from the
    system tray menu.
    """

    def __init__(self, db: SwitchLogger, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._db = db
        self.setWindowTitle("ResumeFlow — Dashboard")
        self.setMinimumSize(620, 480)

        self._setup_ui()

        # Auto-refresh timer
        self._timer = QTimer(self)
        self._timer.timeout.connect(self.refresh)
        self._timer.start(_REFRESH_INTERVAL_MS)

    # -- UI setup ---------------------------------------------------------

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

        self._rate_card_value = QLabel("0")
        self._rate_card = self._make_stat_card(
            self._rate_card_value, "Per Hour", theme.MAUVE
        )
        card_row.addWidget(self._rate_card)

        layout.addLayout(card_row)

        # ── Score progress bar ──
        self._progress = QProgressBar()
        self._progress.setRange(0, 100)
        self._progress.setValue(0)
        self._progress.setFixedHeight(16)
        self._progress.setFormat("  0/100")
        layout.addWidget(self._progress)

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
        self._table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        layout.addWidget(self._table, 1)

        self.refresh()

    # -- helpers ----------------------------------------------------------

    def _make_stat_card(
        self, value_label: QLabel, subtitle: str, color: str
    ) -> QWidget:
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

    # -- public -----------------------------------------------------------

    def refresh(self) -> None:
        """Re-read stats from the database and update the UI."""
        try:
            score_data = self._db.daily_score()
            score = score_data["score"]
            total = score_data["total_today"]
            per_hour = score_data["per_hour"]
            color = score_color(score)

            self._score_card_value.setText(str(score))
            self._score_card_value.setStyleSheet(f"color: {color};")
            self._switches_card_value.setText(str(total))
            self._rate_card_value.setText(str(per_hour))

            self._progress.setValue(score)
            self._progress.setFormat(f"  {score}/100")
            self._progress.setStyleSheet(f"""
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
        except Exception:
            logger.exception("Error refreshing dashboard stats")

        try:
            switches = self._db.recent_switches(50)
            self._table.setRowCount(len(switches))
            for row, entry in enumerate(switches):
                ts = entry.get("timestamp", 0)
                time_str = datetime.fromtimestamp(ts).strftime("%H:%M:%S") if ts else ""
                time_item = QTableWidgetItem(time_str)
                time_item.setTextAlignment(int(Qt.AlignmentFlag.AlignCenter))
                self._table.setItem(row, 0, time_item)

                from_item = QTableWidgetItem(str(entry.get("from_window", "")))
                self._table.setItem(row, 1, from_item)

                to_item = QTableWidgetItem(str(entry.get("to_window", "")))
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
        except Exception:
            logger.exception("Error refreshing dashboard table")

    def cleanup(self) -> None:
        """Stop the refresh timer."""
        self._timer.stop()

    # -- overrides --------------------------------------------------------

    def closeEvent(self, event) -> None:  # noqa: N802
        """Hide instead of closing so the window can be reopened."""
        event.ignore()
        self.hide()
