"""
LuxSense Pro — Core Configuration and Storage Management
Handles persistent user settings, calibration profiles, and historical measurements.
Data is stored in standard OS application data directories so it survives application updates.
"""

import os
import sys
import json
import sqlite3
from pathlib import Path
from dataclasses import dataclass, asdict
from typing import Dict, Any, Optional, List

APP_NAME = "LuxSense Pro"
APP_IDENTIFIER = "LuxSensePro"
APP_VERSION = "2.1.0"
ORG_NAME = "DevPro-CORP"
GITHUB_OWNER = "DevPro-CORPORATION"
GITHUB_REPO = "luxsense-pro"
DEFAULT_SERIAL_PORT = "COM5"
DEFAULT_BAUD_RATE = 115200

def get_app_data_dir() -> Path:
    """Return standard user data directory for LuxSense Pro."""
    if sys.platform == "win32":
        base = os.environ.get("APPDATA") or os.path.expanduser("~\\AppData\\Roaming")
        data_dir = Path(base) / "DevPro" / APP_IDENTIFIER
    elif sys.platform == "darwin":
        data_dir = Path.home() / "Library" / "Application Support" / "DevPro" / APP_IDENTIFIER
    else:
        data_dir = Path.home() / ".config" / "devpro" / "luxsense-pro"
    data_dir.mkdir(parents=True, exist_ok=True)
    return data_dir

@dataclass
class UserSettings:
    serial_port: str = DEFAULT_SERIAL_PORT
    baud_rate: int = DEFAULT_BAUD_RATE
    auto_check_updates: bool = True
    check_interval_hours: int = 24
    include_prereleases: bool = False
    last_update_check: Optional[str] = None
    postponed_version: Optional[str] = None
    telemetry_logging: bool = True
    theme: str = "graphite_dark"

    @classmethod
    def load(cls) -> "UserSettings":
        path = get_app_data_dir() / "settings.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f"[Storage] Warning: Failed to load settings ({e}), using defaults.")
        settings = cls()
        settings.save()
        return settings

    def save(self) -> None:
        path = get_app_data_dir() / "settings.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            print(f"[Storage] Error saving settings: {e}")

@dataclass
class CalibrationProfile:
    profile_name: str = "Standard Factory (BH1750)"
    zero_offset: float = 0.0          # Additive correction in lx
    gain_multiplier: float = 1.0       # Multiplicative scaling
    calibrated_at: str = "2026-11-12"
    notes: str = "Standard BH1750 high-resolution mode (1 lx resolution)"

    @classmethod
    def load(cls) -> "CalibrationProfile":
        path = get_app_data_dir() / "calibration.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                return cls(**{k: v for k, v in data.items() if k in cls.__dataclass_fields__})
            except Exception as e:
                print(f"[Storage] Warning: Failed to load calibration ({e}), using defaults.")
        profile = cls()
        profile.save()
        return profile

    def save(self) -> None:
        path = get_app_data_dir() / "calibration.json"
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(asdict(self), f, indent=2)
        except Exception as e:
            print(f"[Storage] Error saving calibration: {e}")

    def apply(self, raw_lux: float) -> float:
        """Apply calibration equation: (raw + offset) * gain."""
        corrected = (raw_lux + self.zero_offset) * self.gain_multiplier
        return max(0.0, round(corrected, 2))

class MeasurementHistory:
    """SQLite-backed persistent measurement history."""
    def __init__(self):
        self.db_path = get_app_data_dir() / "history.db"
        self._init_db()

    def _init_db(self):
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    raw_lux REAL,
                    calibrated_lux REAL,
                    packet_id INTEGER,
                    port TEXT
                )
            """)
            conn.commit()

    def add_reading(self, raw_lux: float, calibrated_lux: float, packet_id: int, port: str):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO measurements (raw_lux, calibrated_lux, packet_id, port) VALUES (?, ?, ?, ?)",
                    (raw_lux, calibrated_lux, packet_id, port)
                )
                conn.commit()
        except Exception as e:
            print(f"[History] DB insert error: {e}")

    def get_recent(self, limit: int = 50) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT timestamp, raw_lux, calibrated_lux, packet_id, port FROM measurements ORDER BY id DESC LIMIT ?",
                    (limit,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[History] DB query error: {e}")
            return []

    def get_count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements")
                return cursor.fetchone()[0]
        except Exception:
            return 0
