"""
LuxSense Pro — Update Security Module
Provides cryptographic hash verification (SHA-256) and Windows Authenticode
digital signature validation to guarantee binary integrity and authenticity.
"""

import os
import sys
import hashlib
import subprocess
from pathlib import Path
from typing import Tuple, Optional

def compute_sha256(filepath: Path) -> str:
    """Computes SHA-256 hex digest of the given file in 64KB chunks."""
    sha256 = hashlib.sha256()
    with open(filepath, "rb") as f:
        while chunk := f.read(65536):
            sha256.update(chunk)
    return sha256.hexdigest().lower()

def verify_sha256(filepath: Path, expected_hash: str) -> bool:
    """Verifies that the file matches the expected SHA-256 hash (case-insensitive)."""
    if not filepath.exists():
        return False
    actual_hash = compute_sha256(filepath)
    return actual_hash.strip().lower() == expected_hash.strip().lower()

def verify_authenticode(filepath: Path, expected_subject: Optional[str] = "DevPro") -> Tuple[bool, str]:
    """
    Verifies Windows Authenticode digital signature on an executable or installer.
    Returns (is_valid, details_message).
    """
    if sys.platform != "win32":
        return True, "Authenticode check only applicable on Windows platforms."

    if not filepath.exists():
        return False, f"File does not exist: {filepath}"

    ps_cmd = (
        f"$sig = Get-AuthenticodeSignature -FilePath '{filepath}'; "
        f"$cert = $sig.SignerCertificate; "
        f"[PSCustomObject]@{{ "
        f"Status = $sig.Status.ToString(); "
        f"StatusMsg = $sig.StatusMessage; "
        f"Subject = if ($cert) {{ $cert.Subject }} else {{ '' }}; "
        f"Issuer = if ($cert) {{ $cert.Issuer }} else {{ '' }}; "
        f"Thumbprint = if ($cert) {{ $cert.Thumbprint }} else {{ '' }} "
        f"}} | ConvertTo-Json -Compress"
    )

    try:
        res = subprocess.run(
            ["powershell.exe", "-NoProfile", "-NonInteractive", "-Command", ps_cmd],
            capture_output=True,
            text=True,
            timeout=15
        )
        if res.returncode == 0 and res.stdout.strip():
            import json
            data = json.loads(res.stdout.strip())
            status = data.get("Status", "Unknown")
            subject = data.get("Subject", "")

            if status == "Valid":
                if expected_subject and expected_subject.lower() not in subject.lower():
                    return False, f"Signed, but publisher '{subject}' does not match expected '{expected_subject}'."
                return True, f"Valid Authenticode signature from: {subject}"
            elif status == "NotSigned":
                return False, "Binary is not digitally signed (Status: NotSigned)."
            else:
                return False, f"Authenticode check failed: {status} ({data.get('StatusMsg', '')})"
        else:
            return False, f"PowerShell Authenticode check failed: {res.stderr.strip()}"
    except Exception as e:
        return False, f"Authenticode inspection exception: {e}"
