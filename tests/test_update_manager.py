"""
Unit Tests for LuxSense Pro Update Manager, Channels & SemVer Verification
"""

import pytest
from packaging.version import parse as parse_version
from updater.manifest import ReleaseManifest, parse_sha256sums
from software.core.config import APP_VERSION

def test_semver_comparisons():
    current = parse_version(APP_VERSION)
    newer = parse_version("2.4.0")
    patch = parse_version("2.3.1")
    older = parse_version("2.2.0")

    assert newer > current
    assert patch > current
    assert older < current

def test_downgrade_prevention():
    installed = parse_version("2.1.0")
    candidate_older = parse_version("2.0.0")
    candidate_same = parse_version("2.1.0")

    assert not (candidate_older > installed)
    assert not (candidate_same > installed)

def test_stable_channel_filtering():
    releases = [
        {"tag_name": "v2.0.0", "prerelease": False},
        {"tag_name": "v2.1.0", "prerelease": False},
        {"tag_name": "v2.2.0-beta.1", "prerelease": True},
        {"tag_name": "v2.2.0-rc.1", "prerelease": True},
        {"tag_name": "v2.2.0", "prerelease": False}
    ]

    # In Stable channel, filter out prereleases and beta/rc tags
    stable_only = [
        r for r in releases
        if not r["prerelease"] and not any(x in r["tag_name"].lower() for x in ["beta", "rc", "alpha"])
    ]
    assert len(stable_only) == 3
    assert all("beta" not in r["tag_name"] for r in stable_only)
    assert all("rc" not in r["tag_name"] for r in stable_only)

def test_beta_channel_inclusion():
    releases = [
        {"tag_name": "v2.0.0", "prerelease": False},
        {"tag_name": "v2.1.0", "prerelease": False},
        {"tag_name": "v2.2.0-beta.1", "prerelease": True}
    ]

    installed = parse_version("2.1.0")
    # Beta channel evaluates all releases
    best_ver = None
    for r in releases:
        v = parse_version(r["tag_name"].lstrip("v"))
        if best_ver is None or v > best_ver:
            best_ver = v

    assert best_ver == parse_version("2.2.0-beta.1")
    assert best_ver > installed

def test_release_manifest_parsing():
    manifest_json = """{
        "version": "2.1.0",
        "tag_name": "v2.1.0",
        "release_name": "LuxSense Pro v2.1.0",
        "published_at": "2026-11-13T20:00:00Z",
        "prerelease": false,
        "release_notes": "Official release notes",
        "assets": {
            "installer": {
                "filename": "LuxSense-Pro-Setup-v2.1.0.exe",
                "sha256": "a0a80e4060d152cb33cd9233f6072e9af1450774f8418c0565ccc65f05c3b478",
                "url": "https://github.com/DevPro-CORPORATION/luxsense-pro/releases/download/v2.1.0/installer.exe",
                "size": 39500000
            }
        }
    }"""
    manifest = ReleaseManifest.from_json_str(manifest_json)
    assert manifest.version == "2.1.0"
    assert manifest.tag_name == "v2.1.0"
    assert not manifest.prerelease
    assert manifest.channel == "stable"
    installer = manifest.get_asset("installer")
    assert installer is not None
    assert installer.filename == "LuxSense-Pro-Setup-v2.1.0.exe"
    assert len(installer.sha256) == 64

def test_sha256sums_parser():
    sample_text = """
    # SHA-256 Checksums
    e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855  empty.txt
    ba7816bf8f01cfea414140de5dae2223b00361a396177a9cb410ff61f20015ad *abc.bin
    """
    parsed = parse_sha256sums(sample_text)
    assert "empty.txt" in parsed
    assert "abc.bin" in parsed
    assert parsed["empty.txt"] == "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855"
