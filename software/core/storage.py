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
APP_VERSION = "2.3.3"
ORG_NAME = "DevPro-CORP"
GITHUB_OWNER = "DevPro-CORPORATION"
GITHUB_REPO = "LuxSense-Pro"
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

def is_newer_version(cand: str, base: Optional[str]) -> bool:
    """Return True if cand version is strictly greater than base version."""
    if not cand or not base:
        return False
    try:
        from packaging.version import parse as parse_ver
        return parse_ver(cand) > parse_ver(base)
    except Exception:
        def _to_tuple(v: str):
            clean = "".join(c for c in v if c.isdigit() or c == ".").strip(".")
            return tuple(int(x) for x in clean.split(".") if x.isdigit())
        try:
            return _to_tuple(cand) > _to_tuple(base)
        except Exception:
            return False

@dataclass
class UserSettings:
    serial_port: str = DEFAULT_SERIAL_PORT
    baud_rate: int = DEFAULT_BAUD_RATE
    update_channel: str = "stable"       # "stable" or "beta"
    auto_check_updates: bool = True
    last_update_check: Optional[str] = None
    latest_known_version: str = APP_VERSION
    postponed_version: Optional[str] = None
    telemetry_logging: bool = True
    theme: str = "dark"                  # "dark" (default) or "light"
    last_acknowledged_version: Optional[str] = None
    previous_version: Optional[str] = None

    def __post_init__(self):
        if self.theme not in ("dark", "light"):
            self.theme = "dark"

    def should_show_changelog(self) -> bool:
        """
        Returns True only if an existing installation upgraded to a newer APP_VERSION.
        Returns False on first launch, repeated launches of the same version, and failed updates/rollbacks.
        """
        if not self.last_acknowledged_version:
            return False
        return is_newer_version(APP_VERSION, self.last_acknowledged_version)

    def acknowledge_version(self, version: str) -> None:
        """Persist acknowledgement of version changelog card."""
        self.last_acknowledged_version = version
        self.previous_version = None
        self.save()

    @classmethod
    def load(cls) -> "UserSettings":
        path = get_app_data_dir() / "settings.json"
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                # Normalize legacy theme names to strictly 2 modes: dark (default) or light
                if data.get("theme") in ("graphite_dark", "night", "system"):
                    data["theme"] = "dark"
                elif data.get("theme") not in ("dark", "light"):
                    data["theme"] = "dark"

                # Check version progression
                stored_ack = data.get("last_acknowledged_version")
                if not stored_ack:
                    # If upgrading from an older installation that did not track last_acknowledged_version
                    stored_ack = data.get("latest_known_version") or "2.3.0"
                    data["last_acknowledged_version"] = stored_ack

                prev = None
                if stored_ack and is_newer_version(APP_VERSION, stored_ack):
                    prev = stored_ack

                settings = cls(
                    **{k: v for k, v in data.items() if k in cls.__dataclass_fields__}
                )
                if prev:
                    settings.previous_version = prev
                return settings
            except Exception as e:
                print(f"[Storage] Warning: Failed to load settings ({e}), using defaults.")
        # Brand new first launch: record current APP_VERSION so changelog doesn't pop up on cold install
        settings = cls(last_acknowledged_version=APP_VERSION)
        settings.save()
        return settings

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

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
    calibrated_at: str = "2026-11-13"
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

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)

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
                CREATE TABLE IF NOT EXISTS sessions (
                    session_id TEXT PRIMARY KEY,
                    name TEXT,
                    operator TEXT,
                    lighting_type TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    min_threshold REAL DEFAULT 300.0,
                    max_threshold REAL DEFAULT 750.0,
                    notes TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS measurements (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    session_id TEXT DEFAULT 'default',
                    raw_lux REAL,
                    calibrated_lux REAL,
                    packet_id INTEGER,
                    port TEXT
                )
            """)
            conn.execute("""
                CREATE TABLE IF NOT EXISTS spatial_points (
                    point_id TEXT PRIMARY KEY,
                    session_id TEXT DEFAULT 'default',
                    label TEXT,
                    x_m REAL,
                    y_m REAL,
                    measured_lux REAL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            # Ensure default session exists
            conn.execute("""
                INSERT OR IGNORE INTO sessions (session_id, name, operator, lighting_type, notes)
                VALUES ('default', 'Standard Laboratory Session', 'DevPro Technician', 'Broadband Ambient', 'Default continuous baseline recording')
            """)
            # Automatic column migration if table already existed
            cursor = conn.execute("PRAGMA table_info(measurements)")
            cols = [c[1] for c in cursor.fetchall()]
            if "session_id" not in cols:
                conn.execute("ALTER TABLE measurements ADD COLUMN session_id TEXT DEFAULT 'default'")
            conn.commit()

    def add_reading(self, raw_lux: float, calibrated_lux: float, packet_id: int, port: str, session_id: str = "default"):
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT INTO measurements (session_id, raw_lux, calibrated_lux, packet_id, port) VALUES (?, ?, ?, ?, ?)",
                    (session_id, raw_lux, calibrated_lux, packet_id, port)
                )
                conn.commit()
        except Exception as e:
            print(f"[History] DB insert error: {e}")

    def get_recent(self, limit: int = 50, session_id: Optional[str] = None) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                if session_id:
                    cursor = conn.execute(
                        "SELECT timestamp, raw_lux, calibrated_lux, packet_id, port, session_id FROM measurements WHERE session_id = ? ORDER BY id DESC LIMIT ?",
                        (session_id, limit)
                    )
                else:
                    cursor = conn.execute(
                        "SELECT timestamp, raw_lux, calibrated_lux, packet_id, port, session_id FROM measurements ORDER BY id DESC LIMIT ?",
                        (limit,)
                    )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[History] DB query error: {e}")
            return []

    def create_session(self, session_id: str, name: str, operator: str, lighting_type: str, min_th: float, max_th: float, notes: str) -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO sessions (session_id, name, operator, lighting_type, min_threshold, max_threshold, notes) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (session_id, name, operator, lighting_type, min_th, max_th, notes)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"[History] Create session error: {e}")
            return False

    def list_sessions(self) -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute("SELECT * FROM sessions ORDER BY created_at DESC")
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[History] List sessions error: {e}")
            return []

    def add_spatial_point(self, point_id: str, label: str, x_m: float, y_m: float, measured_lux: float, session_id: str = "default") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "INSERT OR REPLACE INTO spatial_points (point_id, session_id, label, x_m, y_m, measured_lux) VALUES (?, ?, ?, ?, ?, ?)",
                    (point_id, session_id, label, x_m, y_m, measured_lux)
                )
                conn.commit()
                return True
        except Exception as e:
            print(f"[History] Add spatial point error: {e}")
            return False

    def get_spatial_points(self, session_id: str = "default") -> List[Dict[str, Any]]:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.execute(
                    "SELECT point_id, session_id, label, x_m, y_m, measured_lux, timestamp FROM spatial_points WHERE session_id = ? ORDER BY point_id ASC",
                    (session_id,)
                )
                return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"[History] Get spatial points error: {e}")
            return []

    def clear_spatial_points(self, session_id: str = "default") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("DELETE FROM spatial_points WHERE session_id = ?", (session_id,))
                conn.commit()
                return True
        except Exception as e:
            print(f"[History] Clear spatial points error: {e}")
            return False

    def get_count(self) -> int:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM measurements")
                return cursor.fetchone()[0]
        except Exception:
            return 0

    def export_to_csv(self, filepath: str) -> str:
        import csv
        records = self.get_recent(10000)
        os.makedirs(os.path.dirname(os.path.abspath(filepath)), exist_ok=True)
        with open(filepath, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["ID", "Timestamp", "Session", "Packet_ID", "Raw_Lux", "Calibrated_Lux", "Port"])
            for r in records:
                writer.writerow([
                    r.get("id", ""),
                    r.get("timestamp", ""),
                    r.get("session_id", "default"),
                    r.get("packet_id", ""),
                    r.get("raw_lux", ""),
                    r.get("calibrated_lux", ""),
                    r.get("port", "")
                ])
        return filepath


