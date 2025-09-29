#!/usr/bin/env python3
"""
Test governance-flake foundation implementation
テスト対象: governance/flake.nix の基盤構築と最小チェック実行
"""

import subprocess
import pytest
from pathlib import Path

def test_governance_flake_provides_dev_shell():
    """governance/flake.nixがdevShellを提供することを確認"""
    governance_dir = Path("governance")
    flake_path = governance_dir / "flake.nix"

    # governance/flake.nixが存在することを確認
    assert flake_path.exists(), f"governance/flake.nix must exist at {flake_path}"

    # devShellが利用可能であることを確認
    result = subprocess.run(
        ["nix", "flake", "show"],
        capture_output=True,
        text=True,
        cwd=governance_dir
    )
    assert result.returncode == 0, f"nix flake show failed: {result.stderr}"
    assert "devShells" in result.stdout, "devShells must be provided"

def test_governance_flake_provides_formatter():
    """governance/flake.nixがformatterを提供することを確認"""
    governance_dir = Path("governance")

    result = subprocess.run(
        ["nix", "flake", "show"],
        capture_output=True,
        text=True,
        cwd=governance_dir
    )
    assert result.returncode == 0, f"nix flake show failed: {result.stderr}"
    assert "formatter" in result.stdout, "formatter must be provided"

def test_governance_flake_provides_checks():
    """governance/flake.nixがchecksを提供することを確認"""
    governance_dir = Path("governance")

    result = subprocess.run(
        ["nix", "flake", "show"],
        capture_output=True,
        text=True,
        cwd=governance_dir
    )
    assert result.returncode == 0, f"nix flake show failed: {result.stderr}"
    assert "checks" in result.stdout, "checks must be provided"

def test_governance_dir_cue_srp_declaration():
    """governance/dir.cueがSRP（契約と検査の提供のみ）を明記していることを確認"""
    governance_dir = Path("governance")
    dir_cue_path = governance_dir / "dir.cue"

    assert dir_cue_path.exists(), f"governance/dir.cue must exist at {dir_cue_path}"

    content = dir_cue_path.read_text()
    assert "契約と検査の提供のみ" in content, "SRP declaration must be present"
    assert "srp:" in content, "srp field must be present"

def test_root_nix_flake_check_succeeds():
    """ルートディレクトリでnix flake checkが成功することを確認"""
    result = subprocess.run(
        ["nix", "flake", "check", "--no-build"],
        capture_output=True,
        text=True,
        timeout=30
    )
    assert result.returncode == 0, f"nix flake check failed: {result.stderr}"