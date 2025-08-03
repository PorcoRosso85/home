"""E2Eテスト: 統合similarityアプリの動作確認"""
import subprocess
import pytest


def test_e2e_similarity_app_shows_help():
    """統合similarityアプリがヘルプメッセージを表示することを確認"""
    result = subprocess.run(
        ["nix", "run", "/home/nixos/bin/src/poc/similarity#similarity"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "similarity" in result.stdout.lower()
    assert any(lang in result.stdout for lang in ["ts", "py", "rs"])
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()


def test_e2e_similarity_app_with_args_shows_help():
    """引数付きでもヘルプを表示することを確認"""
    result = subprocess.run(
        ["nix", "run", "/home/nixos/bin/src/poc/similarity#similarity", "--", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "similarity" in result.stdout.lower()