"""
LuxSense Pro — Automated Packaging & Installer Distribution Pipeline
Compiles binaries, packages Inno Setup installer, generates SHA-256 checksums,
and produces release-manifest.json and SHA256SUMS.txt.
"""

import os
import sys
import json
import shutil
import hashlib
import zipfile
import subprocess
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parents[1]
APP_VERSION = "2.1.0"
DIST_DIR = ROOT_DIR / "dist"
INSTALLER_DIR = ROOT_DIR / "dist_installer"
ISCC_PATH = Path(r"C:\Users\AIMLOPS\AppData\Local\Programs\Inno Setup 6\ISCC.exe")

def compute_sha256(filepath: Path) -> str:
    sha = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha.update(chunk)
    return sha.hexdigest().lower()

def step_compile_app():
    print("--- [1/6] Compiling LuxSense Pro Desktop Application with PyInstaller ---")
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['app/main.py'],
    pathex=['{str(ROOT_DIR).replace(os.sep, "/")}'],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6', 'serial', 'serial.tools.list_ports', 'packaging'],
    hookspath=[],
    hooksconfig={{}},
    runtime_hooks=[],
    excludes=[],
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
    print("--- [2/6] Compiling Standalone Updater Bootstrapper ---")
    spec_path = ROOT_DIR / "updater_bootstrapper" / "bootstrapper.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(DIST_DIR), str(spec_path)]
    subprocess.run(cmd, check=True, cwd=str(ROOT_DIR / "updater_bootstrapper"))
    print("Compiled updater.exe successfully.")

def step_build_inno_installer():
    print("--- [3/6] Compiling Windows Installer with Inno Setup ---")
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    iss_file = ROOT_DIR / "installer" / "LuxSensePro_Setup.iss"

    if ISCC_PATH.exists():
        cmd = [str(ISCC_PATH), str(iss_file)]
        subprocess.run(cmd, check=True, cwd=str(ROOT_DIR))
        print("Built LuxSense-Pro-Setup-v2.1.0.exe successfully.")
    else:
        print(f"Warning: ISCC not found at {ISCC_PATH}, searching PATH...")
        subprocess.run(["iscc", str(iss_file)], check=True, cwd=str(ROOT_DIR))

def step_package_portable_zip():
    print("--- [4/6] Creating Portable Distribution ZIP ---")
    zip_path = INSTALLER_DIR / f"LuxSense-Pro-v{APP_VERSION}-portable.zip"
    with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
        for f in [DIST_DIR / "LuxSensePro.exe", DIST_DIR / "updater.exe", ROOT_DIR / "my_icon.ico", ROOT_DIR / "README.md", ROOT_DIR / "LICENSE"]:
            if f.exists():
                z.write(f, arcname=f.name)
        ino_file = ROOT_DIR / "firmware" / "LuxSense_Arduino" / "LuxSense_Arduino.ino"
        if ino_file.exists():
            z.write(ino_file, arcname="firmware/LuxSense_Arduino.ino")
    print(f"Created portable zip: {zip_path.name}")

def step_generate_checksums_and_manifest():
    print("--- [5/6] Generating SHA-256 Checksums & Release Manifest ---")
    sums_file = INSTALLER_DIR / "SHA256SUMS.txt"
    manifest_file = INSTALLER_DIR / "release-manifest.json"

    files_to_hash = [
        INSTALLER_DIR / f"LuxSense-Pro-Setup-v{APP_VERSION}.exe",
        INSTALLER_DIR / f"LuxSense-Pro-v{APP_VERSION}-portable.zip",
        DIST_DIR / "updater.exe"
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
                "url": f"https://github.com/DevPro-CORPORATION/luxsense-pro/releases/download/v{APP_VERSION}/{f.name}"
            }

    sums_file.write_text("\n".join(sums_lines) + "\n", encoding="utf-8")

    manifest = {
        "version": APP_VERSION,
        "tag_name": f"v{APP_VERSION}",
        "release_name": f"LuxSense Pro v{APP_VERSION} — Precision Optical Metrology & Release Engine",
        "published_at": "2026-11-12T20:00:00Z",
        "prerelease": False,
        "release_notes": "Official release of LuxSense Pro v2.1.0 with automatic update infrastructure, SHA-256 verification, and persistent data storage.",
        "assets": assets_manifest
    }
    manifest_file.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    print("Generated SHA256SUMS.txt and release-manifest.json successfully.")

def step_sync_website_manifest():
    print("--- [6/6] Syncing Release Information to Product Website ---")
    web_dir = ROOT_DIR / "website"
    web_dir.mkdir(parents=True, exist_ok=True)
    src_manifest = INSTALLER_DIR / "release-manifest.json"
    if src_manifest.exists():
        shutil.copy(src_manifest, web_dir / "releases.json")
        print("Synced releases.json to website/")

def main():
    print(f"=== Starting LuxSense Pro Release Build Pipeline (v{APP_VERSION}) ===")
    step_compile_app()
    step_compile_updater()
    step_build_inno_installer()
    step_package_portable_zip()
    step_generate_checksums_and_manifest()
    step_sync_website_manifest()
    print("=== Release Build Pipeline Completed Successfully ===")

if __name__ == "__main__":
    main()
