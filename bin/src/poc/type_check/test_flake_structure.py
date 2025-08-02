#!/usr/bin/env python3
"""
flake.nixの基本構造をテストする
振る舞い：
- flake checkが成功する
- 各言語の開発シェルが利用可能
- テストコマンドが定義されている
"""

import subprocess
import sys
from pathlib import Path


def test_flake_check():
    """flake checkが成功することを確認"""
    result = subprocess.run(
        ["nix", "flake", "check"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    assert result.returncode == 0, f"flake check failed: {result.stderr}"


def test_dev_shells_available():
    """各言語の開発シェルが定義されていることを確認"""
    required_shells = ["python", "typescript", "go", "rust", "zig"]
    
    for shell in required_shells:
        result = subprocess.run(
            ["nix", "flake", "show", "--json"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        assert result.returncode == 0
        # TODO: JSONパースして devShells.x86_64-linux.{shell} の存在を確認


def test_test_command_available():
    """nix run .#testが定義されていることを確認"""
    result = subprocess.run(
        ["nix", "flake", "show", "--json"],
        capture_output=True,
        text=True,
        cwd=Path(__file__).parent
    )
    assert result.returncode == 0
    # TODO: JSONパースして apps.x86_64-linux.test の存在を確認


if __name__ == "__main__":
    test_flake_check()
    test_dev_shells_available()
    test_test_command_available()
    print("All tests passed!")