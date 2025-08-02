"""Data models for flake graph."""

from pathlib import Path
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


class FlakeDependency(BaseModel):
    """Represents a dependency between flakes."""
    
    name: str
    url: str
    is_local: bool = Field(default=False)
    path: Optional[Path] = None


class FlakeInfo(BaseModel):
    """Represents information extracted from a flake.nix file."""
    
    path: Path
    description: str
    dependencies: List[FlakeDependency] = Field(default_factory=list)
    outputs: List[str] = Field(default_factory=list)
    apps: List[str] = Field(default_factory=list)
    language: Optional[str] = None
    category: Optional[str] = None
    
    def get_responsibility(self) -> str:
        """Extract the main responsibility from description."""
        return self.description
    
    def get_id(self) -> str:
        """Generate unique ID based on path."""
        # Convert absolute path to relative path from bin/src
        try:
            relative = self.path.relative_to("/home/nixos/bin/src")
            return str(relative.parent)
        except ValueError:
            return str(self.path.parent)