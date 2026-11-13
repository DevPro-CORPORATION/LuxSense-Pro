"""
LuxSense Pro — Central Configuration & Constants
"""

from software.core.storage import (
    APP_NAME,
    APP_IDENTIFIER,
    APP_VERSION,
    ORG_NAME,
    GITHUB_OWNER,
    GITHUB_REPO,
    DEFAULT_SERIAL_PORT,
    DEFAULT_BAUD_RATE,
    UserSettings,
    CalibrationProfile,
    MeasurementHistory,
    get_app_data_dir
)

SECRET_KEY = bytes([
    0x4A, 0x91, 0x2C, 0x7E, 0x10, 0xF3, 0x88, 0x5B,
    0xD2, 0x64, 0x39, 0xA7, 0x05, 0xE1, 0x4F, 0xB8
])
HANDSHAKE_TEXT = "ID:GY30_LUX_PRO_2026"
DISCOVER_COMMAND = b"DISCOVER_LUX_SENSOR\n"
DISCONNECT_COMMAND = b"DISCONNECT\n"

# GitHub REST API configuration
GITHUB_API_RELEASES_URL = f"https://api.github.com/repos/{GITHUB_OWNER}/{GITHUB_REPO}/releases"
GITHUB_REPO_URL = f"https://github.com/{GITHUB_OWNER}/{GITHUB_REPO}"
ISSUES_NEW_BUG_URL = f"{GITHUB_REPO_URL}/issues/new?template=bug_report.md"
ISSUES_NEW_FEATURE_URL = f"{GITHUB_REPO_URL}/issues/new?template=feature_request.md"

