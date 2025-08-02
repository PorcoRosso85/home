"""Minimal flake scanner."""

import re
from pathlib import Path
from typing import Optional


def scan_flake_description(flake_path: Path) -> Optional[str]:
    """Extract description from a flake.nix file."""
    try:
        content = flake_path.read_text()
        # Simple regex to find description
        match = re.search(r'description\s*=\s*"([^"]+)"', content)
        if match:
            return match.group(1)
        return None
    except Exception:
        return None