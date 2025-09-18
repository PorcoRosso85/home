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


def scan_readme_content(flake_dir: Path) -> Optional[str]:
    """Read README.md content from a flake directory."""
    readme_path = flake_dir / "README.md"
    if readme_path.exists():
        try:
            return readme_path.read_text()
        except Exception:
            return None
    return None