"""Test flake models."""

from pathlib import Path

import pytest

from flake_graph.models import FlakeDependency, FlakeInfo


def test_flake_dependency_creation():
    """Test FlakeDependency model creation."""
    dep = FlakeDependency(
        name="nixpkgs",
        url="github:NixOS/nixpkgs/nixos-unstable"
    )
    assert dep.name == "nixpkgs"
    assert dep.url == "github:NixOS/nixpkgs/nixos-unstable"
    assert dep.is_local is False
    assert dep.path is None


def test_flake_dependency_local():
    """Test local FlakeDependency."""
    dep = FlakeDependency(
        name="kuzu-py",
        url="path:/home/nixos/bin/src/persistence/kuzu_py",
        is_local=True,
        path=Path("/home/nixos/bin/src/persistence/kuzu_py")
    )
    assert dep.is_local is True
    assert dep.path == Path("/home/nixos/bin/src/persistence/kuzu_py")


def test_flake_info_creation():
    """Test FlakeInfo model creation."""
    info = FlakeInfo(
        path=Path("/home/nixos/bin/src/persistence/kuzu_py/flake.nix"),
        description="KuzuDB thin wrapper for Python"
    )
    assert info.path == Path("/home/nixos/bin/src/persistence/kuzu_py/flake.nix")
    assert info.description == "KuzuDB thin wrapper for Python"
    assert info.dependencies == []
    assert info.outputs == []
    assert info.apps == []
    assert info.language is None
    assert info.category is None


def test_flake_info_get_responsibility():
    """Test getting responsibility from FlakeInfo."""
    info = FlakeInfo(
        path=Path("/home/nixos/bin/src/test/flake.nix"),
        description="Test flake for unit testing"
    )
    assert info.get_responsibility() == "Test flake for unit testing"


def test_flake_info_get_id():
    """Test getting ID from FlakeInfo."""
    info = FlakeInfo(
        path=Path("/home/nixos/bin/src/persistence/kuzu_py/flake.nix"),
        description="KuzuDB wrapper"
    )
    assert info.get_id() == "persistence/kuzu_py"


def test_flake_info_get_id_outside_src():
    """Test getting ID from FlakeInfo when path is outside bin/src."""
    info = FlakeInfo(
        path=Path("/home/nixos/other/test/flake.nix"),
        description="Test flake"
    )
    # Should return the parent directory path when not under bin/src
    assert info.get_id() == "/home/nixos/other/test"