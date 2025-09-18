"""Functional data structures for flake graph."""

from pathlib import Path
from typing import Dict, List, Optional, TypedDict


class FlakeDependencyDict(TypedDict, total=False):
    """Dictionary structure for flake dependency."""
    name: str
    url: str
    is_local: bool
    path: Optional[Path]


class FlakeInfoDict(TypedDict, total=False):
    """Dictionary structure for flake information."""
    path: Path
    description: str
    dependencies: List[FlakeDependencyDict]
    outputs: List[str]
    apps: List[str]
    language: Optional[str]
    category: Optional[str]


def create_dependency(
    name: str, 
    url: str, 
    is_local: bool = False, 
    path: Optional[Path] = None
) -> FlakeDependencyDict:
    """Create a flake dependency dictionary."""
    dep: FlakeDependencyDict = {"name": name, "url": url, "is_local": is_local}
    if path:
        dep["path"] = path
    return dep


def create_flake_info(
    path: Path,
    description: str,
    dependencies: Optional[List[FlakeDependencyDict]] = None,
    outputs: Optional[List[str]] = None,
    apps: Optional[List[str]] = None,
    language: Optional[str] = None,
    category: Optional[str] = None
) -> FlakeInfoDict:
    """Create a flake info dictionary."""
    return {
        "path": path,
        "description": description,
        "dependencies": dependencies or [],
        "outputs": outputs or [],
        "apps": apps or [],
        "language": language,
        "category": category
    }


def get_flake_responsibility(flake: FlakeInfoDict) -> str:
    """Extract the main responsibility from description."""
    return flake["description"]


def get_flake_id(flake: FlakeInfoDict) -> str:
    """Generate unique ID based on path."""
    try:
        relative = flake["path"].relative_to("/home/nixos/bin/src")
        return str(relative.parent)
    except ValueError:
        return str(flake["path"].parent)