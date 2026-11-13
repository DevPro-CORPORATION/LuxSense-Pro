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
    print("--- [1/5] Compiling LuxSense Pro Desktop Application with PyInstaller ---")
    spec_content = f"""# -*- mode: python ; coding: utf-8 -*-
a = Analysis(
    ['software/main.py'],
    pathex=['{str(ROOT_DIR).replace(os.sep, "/")}'],
    binaries=[],
    datas=[],
    hiddenimports=['PyQt6', 'serial', 'serial.tools.list_ports', 'packaging', 'updater', 'software'],
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
    print("--- [2/5] Compiling Standalone Updater Bootstrapper ---")
    spec_path = ROOT_DIR / "updater" / "bootstrapper.spec"
    cmd = [sys.executable, "-m", "PyInstaller", "--noconfirm", "--clean", "--distpath", str(DIST_DIR), str(spec_path)]
    subprocess.run(cmd, check=True, cwd=str(ROOT_DIR / "updater"))
    print("Compiled updater.exe successfully.")

def step_build_inno_installer():
    print("--- [3/5] Compiling Windows Installer with Inno Setup ---")
    INSTALLER_DIR.mkdir(parents=True, exist_ok=True)
    iss_file = ROOT_DIR / "installer" / "LuxSensePro_Setup.iss"

    if ISCC_PATH.exists():
        cmd = [str(ISCC_PATH), str(iss_file)]
        subprocess.run(cmd, check=True, cwd=str(ROOT_DIR))
        print("Built LuxSense-Pro-Setup-v2.1.0.exe successfully.")
    else:
        print(f"Searching for iscc in PATH...")
        subprocess.run(["iscc", str(iss_file)], check=True, cwd=str(ROOT_DIR))

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
        for doc in (ROOT_DIR / "docs").glob("*.md"):
            z.write(doc, arcname=f"docs/{doc.name}")
    print(f"Created portable zip: {zip_path.name}")

def step_generate_checksums_and_manifest():
    print("--- [5/5] Generating SHA-256 Checksums & Release Manifest ---")
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
        "channel": "stable",
        "release_name": f"LuxSense Pro v{APP_VERSION} — Precision Optical Metrology & Release Engine",
        "published_at": "2026-11-13T20:00:00Z",
        "prerelease": False,
        "release_notes": "Official release of LuxSense Pro v2.1.0 featuring an in-app Update Center with Stable and Beta channels, automated GitHub update infrastructure, SHA-256 verification, and persistent AppData user storage.",
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
