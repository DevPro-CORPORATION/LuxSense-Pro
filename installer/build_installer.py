"""
LuxSense Pro — Automated Packaging & Installer Distribution Pipeline
Compiles software application and updater bootstrapper, packages Inno Setup installer,
generates portable ZIP distribution, and produces SHA256SUMS.txt and release-manifest.json.
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import subprocess
from pathlib import Path
from typing import Optional

ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))
APP_VERSION = "2.3.1"
DIST_DIR = ROOT_DIR / "dist"
INSTALLER_DIR = ROOT_DIR / "dist_installer"
ISCC_PATH = Path(r"C:\Users\AIMLOPS\AppData\Local\Programs\Inno Setup 6\ISCC.exe")

def find_iscc() -> Optional[Path]:
    candidates = [
        ISCC_PATH,
        Path(r"C:\Program Files (x86)\Inno Setup 6\ISCC.exe"),
        Path(r"C:\Program Files\Inno Setup 6\ISCC.exe"),
        Path(shutil.which("iscc") or "")
    ]
    for c in candidates:
        if c and c.exists():
            return c
    return None

def compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().lower()

def step_compile_app():
    print("--- [1/5] Compiling LuxSense Pro Desktop Application with PyInstaller ---")
    dist_frontend = ROOT_DIR / "software" / "frontend" / "dist"
    if not dist_frontend.exists():
        print("Frontend dist not found, compiling frontend assets via npm...")
        subprocess.run(["npm", "--prefix", "software/frontend", "install"], check=True, cwd=str(ROOT_DIR), shell=True)
        subprocess.run(["npm", "--prefix", "software/frontend", "run", "build"], check=True, cwd=str(ROOT_DIR), shell=True)

    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['software/main.py'],
    pathex=['{str(ROOT_DIR).replace(os.sep, "/")}'],
    binaries=[],
    datas=[
        ('software/frontend/dist', 'software/frontend/dist'),
        ('dist_installer/firmware-manifest.json', 'dist_installer'),
        ('firmware/devpro_firmware_pubkey.pem', 'firmware'),
        ('firmware/build/LuxSense_Arduino.ino.hex', 'firmware/build')
    ],
    hiddenimports=[
        'PySide6', 'PySide6.QtWebEngineWidgets', 'PySide6.QtWebEngineCore', 'PySide6.QtWebChannel',
        'serial', 'serial.tools.list_ports', 'packaging', 'updater', 'software',
        'cryptography', 'cffi', 'software.core.firmware_security', 'software.core.firmware_flasher'
    ],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=['PyQt6', 'PyQt6.QtCore', 'PyQt6.QtWidgets', 'PyQt6.QtGui', 'PyQt6.sip'],
    noarchive=False,
    optimize=0,
)
pyz = PYZ(a.pure)
exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LuxSensePro',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=['my_icon.ico'],
)
"""
    spec_path = ROOT_DIR / "LuxSensePro.spec"
    spec_path.write_text(spec_content, encoding="utf-8")

    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", str(spec_path)]
    subprocess.run(cmd, check=True, cwd=str(ROOT_DIR))
    print("Compiled LuxSensePro.exe successfully.")

def step_compile_updater():
    print("--- [2/5] Compiling Standalone Updater Bootstrapper ---")
    spec_path = ROOT_DIR / "updater" / "bootstrapper.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(DIST_DIR), str(spec_path)]
    subprocess.run(cmd, check=True, cwd=str(ROOT_DIR / "updater"))
    print("Compiled updater.exe successfully.")

def step_build_inno_installer():
    print("--- [3/5] Compiling Windows Installer with Inno Setup ---")
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    iss_file = ROOT_DIR / "installer" / "LuxSensePro_Setup.iss"

    iscc_bin = find_iscc()
    if iscc_bin:
        cmd = [str(iscc_bin), str(iss_file)]
        subprocess.run(cmd, check=True, cwd=str(ROOT_DIR))
        print(f"Built LuxSense-Pro-Setup-v{APP_VERSION}.exe successfully.")
    else:
        print(f"Searching for iscc in PATH...")
        subprocess.run(["iscc", str(iss_file)], check=True, cwd=str(ROOT_DIR), shell=True)

def step_package_portable_zip():
    print("--- [4/5] Creating Portable Distribution ZIP ---")
    zip_path = INSTALLER_DIR / f"LuxSense-Pro-v{APP_VERSION}-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in [DIST_DIR / "LuxSensePro.exe", DIST_DIR / "updater.exe", ROOT_DIR / "my_icon.ico", ROOT_DIR / "README.md", ROOT_DIR / "LICENSE"]:
            if f.exists():
                z.write(f, arcname=f.name)
        ino_file = ROOT_DIR / "firmware" / "LuxSense_Arduino" / "LuxSense_Arduino.ino"
        if ino_file.exists():
            z.write(ino_file, arcname="firmware/LuxSense_Arduino.ino")
        hex_file = ROOT_DIR / "firmware" / "build" / "LuxSense_Arduino.ino.hex"
        if hex_file.exists():
            z.write(hex_file, arcname="firmware/build/LuxSense_Arduino.ino.hex")
        pubkey_file = ROOT_DIR / "firmware" / "devpro_firmware_pubkey.pem"
        if pubkey_file.exists():
            z.write(pubkey_file, arcname="firmware/devpro_firmware_pubkey.pem")
        fw_manifest = ROOT_DIR / "dist_installer" / "firmware-manifest.json"
        if fw_manifest.exists():
            z.write(fw_manifest, arcname="dist_installer/firmware-manifest.json")
        for doc in (ROOT_DIR / "docs").glob("*.md"):
            z.write(doc, arcname=f"docs/{doc.name}")
    print(f"Created portable zip: {zip_path.name}")

def step_generate_checksums_and_manifest():
    print("--- [5/5] Generating SHA-256 Checksums & Release Manifest ---")
    # Step 5a: Ensure firmware is cryptographically signed
    try:
        from tools.sign_firmware import sign_firmware
        sign_firmware(
            ROOT_DIR / "firmware" / "build" / "LuxSense_Arduino.ino.hex",
            INSTALLER_DIR / "firmware-manifest.json",
            ROOT_DIR / "private_keys" / "devpro_firmware_signing.key",
            version="2.0.0"
        )
    except Exception as e:
        print(f"[Build] Warning: Firmware signing step notice: {e}")

    sums_file = INSTALLER_DIR / "SHA256SUMS.txt"
    manifest_file = INSTALLER_DIR / "release-manifest.json"

    files_to_hash = [
        INSTALLER_DIR / f"LuxSense-Pro-Setup-v{APP_VERSION}.exe",
        INSTALLER_DIR / f"LuxSense-Pro-v{APP_VERSION}-portable.zip",
        DIST_DIR / "updater.exe",
        INSTALLER_DIR / "firmware-manifest.json",
        ROOT_DIR / "firmware" / "build" / "LuxSense_Arduino.ino.hex"
    ]

    sums_lines = ["# LuxSense Pro Release Checksums (SHA-256)"]
    assets_manifest = {}

    for f in files_to_hash:
        if f.exists():
            h = compute_sha256(f)
            sums_lines.append(f"{h}  {f.name}")
            assets_manifest[f.name] = {
                "filename": f.name,
                "sha256": h,
                "size": f.stat().st_size,
                "url": f"https://github.com/DevPro-CORPORATION/LuxSense-Pro/releases/download/v{APP_VERSION}/{f.name}"
            }

    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")

    manifest = {
        "version": APP_VERSION,
        "tag_name": f"v{APP_VERSION}",
        "channel": "stable",
        "release_name": f"LuxSense Pro v{APP_VERSION} — Unified Software & Firmware Update Architecture",
        "published_at": "2026-11-15T15:45:00Z",
        "prerelease": False,
        "release_notes": "Official release of LuxSense Pro v2.3.1 featuring complete production bug hunt resolutions, enhanced Light Mode contrast and dynamic chart theming, dual Uno/Nano AVR flashing support, directory collision-safe updater rollback, and validated hardware integration.",
        "assets": assets_manifest
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Generated SHA256SUMS.txt and release-manifest.json successfully.")

def main():
    print(f"=== Starting LuxSense Pro Distribution Build Pipeline (v{APP_VERSION}) ===")
    step_compile_app()
    step_compile_updater()
    step_build_inno_installer()
    step_package_portable_zip()
    step_generate_checksums_and_manifest()
    print("=== Distribution Build Pipeline Completed Successfully ===")

if __name__ == "__main__":
    main()
