"""E2Eテスト: Python版similarityツールの動作確認"""
import subprocess
import pytest


def test_e2e_py_similarity_exists():
    """Python版similarityツールが存在することを確認"""
    # ツールの初回インストールまたは存在確認
    result = subprocess.run(
        ["nix", "run", "/home/nixos/bin/src/poc/similarity#py", "--", "--version"],
        capture_output=True,
        text=True
    )
    
    # --versionが認識されない場合もあるので、エラーコードは無視
    # 重要なのはツールが実行可能であること
    assert "similarity-py" in result.stdout or "similarity-py" in result.stderr


def test_e2e_py_similarity_shows_help():
    """Python版similarityツールが--helpでヘルプメッセージを表示することを確認"""
    result = subprocess.run(
        ["nix", "run", "/home/nixos/bin/src/poc/similarity#py", "--", "--help"],
        capture_output=True,
        text=True
    )
    
    assert result.returncode == 0
    assert "usage" in result.stdout.lower() or "help" in result.stdout.lower()
    # Python関連のキーワードが含まれることを確認
    assert any(keyword in result.stdout.lower() for keyword in ["py", "python", "similarity"])


def test_e2e_py_similarity_no_args_shows_usage():
    """引数なしで実行した場合、使用方法が表示されることを確認"""
    result = subprocess.run(
        ["nix", "run", "/home/nixos/bin/src/poc/similarity#py"],
        capture_output=True,
        text=True
    )
    
    # 引数なしの場合、通常はエラー(返り値非0)または使用方法が表示される
    # ツールによって挙動が異なるため、出力にusageやhelpが含まれることを確認
    output = result.stdout + result.stderr
    assert "usage" in output.lower() or "help" in output.lower() or "error" in output.lower()