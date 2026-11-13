"""
LuxSense Pro — Release Manifest & Checksum Parser
Handles reading release manifests (JSON) and SHA256SUMS text files.
"""

import json
from dataclasses import dataclass
from typing import Dict, Optional, Any

@dataclass
class ReleaseAssetInfo:
    filename: str
    sha256: str
    url: str
    size: int = 0
    content_type: str = "application/octet-stream"

@dataclass
class ReleaseManifest:
    version: str
    tag_name: str
    release_name: str
    published_at: str
    prerelease: bool
    channel: str
    release_notes: str
    assets: Dict[str, ReleaseAssetInfo]
    raw_json: Optional[Dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ReleaseManifest":
        assets_dict = {}
        for key, asset_data in data.get("assets", {}).items():
            if isinstance(asset_data, dict):
                assets_dict[key] = ReleaseAssetInfo(
                    filename=asset_data.get("filename", ""),
                    sha256=asset_data.get("sha256", "").lower(),
                    url=asset_data.get("url", ""),
                    size=asset_data.get("size", 0),
                    content_type=asset_data.get("content_type", "application/octet-stream")
                )
        prerelease = data.get("prerelease", False)
        return cls(
            version=data.get("version", "").lstrip("v"),
            tag_name=data.get("tag_name", ""),
            release_name=data.get("release_name", ""),
            published_at=data.get("published_at", ""),
            prerelease=prerelease,
            channel="beta" if prerelease else "stable",
            release_notes=data.get("release_notes", ""),
            assets=assets_dict,
            raw_json=data
        )

    @classmethod
    def from_json_str(cls, json_str: str) -> "ReleaseManifest":
        return cls.from_dict(json.loads(json_str))

    def get_asset(self, asset_type: str = "installer") -> Optional[ReleaseAssetInfo]:
        return self.assets.get(asset_type)

def parse_sha256sums(sums_text: str) -> Dict[str, str]:
    """
    Parses SHA256SUMS.txt format: '<hash>  <filename>' or '<hash> *<filename>'.
    Returns dictionary mapping filename -> lowercase sha256.
    """
    mapping = {}
    for line in sums_text.splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        parts = line.split(maxsplit=1)
        if len(parts) == 2:
            sha, fname = parts
            fname = fname.lstrip("* ").strip()
            mapping[fname] = sha.strip().lower()
    return mapping

