"""Settings management with persistence via SQLite."""

import json
import logging
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Optional

from .database import SwitchLogger

logger = logging.getLogger(__name__)

SETTINGS_KEY = "app_settings"


@dataclass
class AppSettings:
    away_threshold: int = 30          # seconds (30-300)
    popup_position: str = "cursor"    # "cursor", "top-right", "bottom-right"
    quiet_hours_start: str = ""       # HH:MM or empty
    quiet_hours_end: str = ""         # HH:MM or empty
    poll_interval: float = 1.0        # seconds
    popup_opacity: float = 0.95
    popup_duration: int = 0           # auto-dismiss seconds (0 = manual)


class SettingsManager:
    """Read / write application settings backed by the SQLite store."""

    def __init__(self, db: SwitchLogger) -> None:
        self._db = db
        self._settings: Optional[AppSettings] = None

    def load(self) -> AppSettings:
        raw = self._db.get_setting(SETTINGS_KEY)
        if raw:
            try:
                data = json.loads(raw)
                self._settings = AppSettings(**{
                    k: v for k, v in data.items()
                    if k in AppSettings.__dataclass_fields__
                })
            except (json.JSONDecodeError, TypeError):
                logger.warning("Corrupt settings in DB; using defaults")
                self._settings = AppSettings()
        else:
            self._settings = AppSettings()
        return self._settings

    def save(self, settings: AppSettings) -> None:
        self._settings = settings
        self._db.set_setting(SETTINGS_KEY, json.dumps(asdict(settings)))
        logger.debug("Settings saved")

    @property
    def current(self) -> AppSettings:
        if self._settings is None:
            return self.load()
        return self._settings

    def is_quiet_hours(self) -> bool:
        settings = self.current
        if not settings.quiet_hours_start or not settings.quiet_hours_end:
            return False
        now = datetime.now()
        current_minutes = now.hour * 60 + now.minute
        try:
            sh, sm = map(int, settings.quiet_hours_start.split(":"))
            eh, em = map(int, settings.quiet_hours_end.split(":"))
        except ValueError:
            return False
        start = sh * 60 + sm
        end = eh * 60 + em
        if start <= end:
            return start <= current_minutes < end
        # Wraps midnight (e.g., 22:00 - 06:00)
        return current_minutes >= start or current_minutes < end
