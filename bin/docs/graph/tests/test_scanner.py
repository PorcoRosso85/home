"""Test flake scanner functionality."""

from pathlib import Path
import tempfile

import pytest

from flake_graph.scanner import scan_flake_description


def test_scan_flake_description_extracts_description():
    """Test that scanner can extract description from flake.nix."""
    flake_content = '''
{
  description = "Test flake for unit testing";
  
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  
  outputs = { self, nixpkgs }: {
    # ...
  };
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='flake.nix', delete=False) as f:
        f.write(flake_content)
        f.flush()
        
        result = scan_flake_description(Path(f.name))
        
    assert result == "Test flake for unit testing"


def test_scan_flake_description_returns_none_for_missing_description():
    """Test that scanner returns None when no description found."""
    flake_content = '''
{
  inputs = {
    nixpkgs.url = "github:NixOS/nixpkgs/nixos-unstable";
  };
  
  outputs = { self, nixpkgs }: {
    # ...
  };
}
'''
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='flake.nix', delete=False) as f:
        f.write(flake_content)
        f.flush()
        
        result = scan_flake_description(Path(f.name))
        
    assert result is None