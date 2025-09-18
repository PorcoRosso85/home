"""環境変数管理のテスト
Run with: nix develop -c uv run pytest test_env.py
"""

import os
import pytest
from infrastructure.variables.env import (
    get_scan_root_path,
    get_db_path,
    get_exclude_patterns,
    get_max_depth,
    should_use_inmemory,
    validate_environment,
)


def test_環境変数取得_必須変数_エラー値返却():
    """必須環境変数が未設定の場合はエラー値を返す"""
    # 環境変数を一時的に削除
    old_value = os.environ.pop("DIRSCAN_ROOT_PATH", None)

    try:
        result = get_scan_root_path()
        assert result["ok"] is False
        assert "DIRSCAN_ROOT_PATH not set" in result["error"]
    finally:
        # 復元
        if old_value:
            os.environ["DIRSCAN_ROOT_PATH"] = old_value


def test_環境変数取得_オプション変数_None返却():
    """オプション環境変数が未設定の場合はNone"""
    # 環境変数を一時的に削除
    old_value = os.environ.pop("DIRSCAN_EXCLUDE_PATTERNS", None)

    try:
        result = get_exclude_patterns()
        assert result is None
    finally:
        # 復元
        if old_value:
            os.environ["DIRSCAN_EXCLUDE_PATTERNS"] = old_value


def test_整数環境変数_正常_整数値返却():
    """整数環境変数の正常ケース"""
    os.environ["DIRSCAN_MAX_DEPTH"] = "5"
    result = get_max_depth()
    assert result["ok"] is True
    assert result["value"] == 5


def test_整数環境変数_無効値_エラー返却():
    """整数環境変数に無効な値"""
    os.environ["DIRSCAN_MAX_DEPTH"] = "invalid"
    result = get_max_depth()
    assert result["ok"] is False
    assert "must be an integer" in result["error"]


def test_inmemoryフラグ_各種値_正しく判定():
    """inmemoryフラグの判定"""
    test_cases = [
        ("true", True),
        ("1", True),
        ("yes", True),
        ("false", False),
        ("0", False),
        ("no", False),
        (None, False),
    ]

    for value, expected in test_cases:
        if value is None:
            os.environ.pop("DIRSCAN_INMEMORY", None)
        else:
            os.environ["DIRSCAN_INMEMORY"] = value

        assert should_use_inmemory() == expected


def test_環境検証_必須変数欠如_エラー返却():
    """環境検証で必須変数の欠如を検出"""
    # 環境変数を一時的に削除
    old_root = os.environ.pop("DIRSCAN_ROOT_PATH", None)
    old_db = os.environ.pop("DIRSCAN_DB_PATH", None)

    try:
        errors = validate_environment()
        assert "DIRSCAN_ROOT_PATH" in errors
        assert "DIRSCAN_DB_PATH" in errors
    finally:
        # 復元
        if old_root:
            os.environ["DIRSCAN_ROOT_PATH"] = old_root
        if old_db:
            os.environ["DIRSCAN_DB_PATH"] = old_db
