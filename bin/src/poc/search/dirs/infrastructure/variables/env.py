#!/usr/bin/env python3
"""
ディレクトリスキャナー環境変数管理
依存: なし
外部依存: なし

規約遵守:
- デフォルト値禁止
- 必須環境変数は明示的にエラー
- 関数として提供（グローバル状態禁止）
"""

import os
from typing import Optional, Dict, Union, TypedDict, Literal


# エラー型定義
class EnvError(TypedDict):
    """環境変数エラー"""

    ok: Literal[False]
    error: str


class EnvSuccess(TypedDict):
    """環境変数成功"""

    ok: Literal[True]
    value: str


EnvResult = Union[EnvSuccess, EnvError]


def _require_env(name: str) -> EnvResult:
    """必須環境変数を取得（デフォルト値なし）

    Args:
        name: 環境変数名

    Returns:
        成功時: EnvSuccess with value
        失敗時: EnvError with error message
    """
    value = os.environ.get(name)
    if not value:
        return EnvError(ok=False, error=f"{name} not set. Set {name}=<value> before running the application")
    return EnvSuccess(ok=True, value=value)


def _optional_env(name: str) -> Optional[str]:
    """オプション環境変数を取得

    Args:
        name: 環境変数名

    Returns:
        環境変数の値またはNone
    """
    return os.environ.get(name)


# 環境変数アクセス関数


def get_scan_root_path() -> EnvResult:
    """スキャン対象のルートパス（必須）

    Returns:
        成功時: EnvSuccess with value
        失敗時: EnvError with error message
    """
    return _require_env("DIRSCAN_ROOT_PATH")


def get_db_path() -> EnvResult:
    """永続化DBパス（必須）

    Returns:
        成功時: EnvSuccess with value
        失敗時: EnvError with error message
    """
    return _require_env("DIRSCAN_DB_PATH")


def get_exclude_patterns() -> Optional[str]:
    """除外パターン（カンマ区切り、オプション）

    Returns:
        カンマ区切りの除外パターンまたはNone
    """
    return _optional_env("DIRSCAN_EXCLUDE_PATTERNS")


class IntSuccess(TypedDict):
    """整数値取得成功"""

    ok: Literal[True]
    value: Optional[int]


class IntError(TypedDict):
    """整数値取得エラー"""

    ok: Literal[False]
    error: str


IntResult = Union[IntSuccess, IntError]


def get_max_depth() -> IntResult:
    """最大スキャン深度（オプション）

    Returns:
        成功時: IntSuccess with value (NoneまたはInt)
        失敗時: IntError with error message
    """
    value = _optional_env("DIRSCAN_MAX_DEPTH")
    if value:
        try:
            return IntSuccess(ok=True, value=int(value))
        except ValueError:
            return IntError(ok=False, error=f"DIRSCAN_MAX_DEPTH must be an integer, got: {value}")
    return IntSuccess(ok=True, value=None)


def should_use_inmemory() -> bool:
    """in-memoryモードを使用するか

    Returns:
        True: in-memoryモード使用
        False: 通常モード
    """
    value = _optional_env("DIRSCAN_INMEMORY")
    if value is None:
        return False
    return value.lower() in ("true", "1", "yes")


def get_fts_index_name(env_value: Optional[str], fallback_value: str) -> str:
    """FTSインデックス名を取得

    Args:
        env_value: 環境変数の値（None可）
        fallback_value: 環境変数が未設定時の値

    Returns:
        環境変数またはフォールバック値
    """
    return env_value or fallback_value


def get_vss_model(env_value: Optional[str], fallback_value: str) -> str:
    """VSS埋め込みモデル名を取得

    Args:
        env_value: 環境変数の値（None可）
        fallback_value: 環境変数が未設定時の値

    Returns:
        環境変数またはフォールバック値
    """
    return env_value or fallback_value


def should_skip_hidden(env_value: Optional[str], fallback_value: bool) -> bool:
    """隠しディレクトリ（.で始まる）をスキップするか

    Args:
        env_value: 環境変数の値（None可）
        fallback_value: 環境変数が未設定時の値

    Returns:
        True: スキップする
        False: スキップしない
    """
    if env_value is None:
        return fallback_value
    return env_value.lower() in ("true", "1", "yes")


# 設定検証


def validate_environment() -> Dict[str, str]:
    """環境設定を検証し、問題があればエラー詳細を返す"""
    errors = {}

    # 必須環境変数チェック
    required = ["DIRSCAN_ROOT_PATH", "DIRSCAN_DB_PATH"]
    for var in required:
        if not os.environ.get(var):
            errors[var] = f"Required environment variable {var} is not set"

    # パスの存在チェック（ルートパス）
    root_path = os.environ.get("DIRSCAN_ROOT_PATH")
    if root_path and not os.path.exists(root_path):
        errors["DIRSCAN_ROOT_PATH"] = f"Path does not exist: {root_path}"

    return errors


# テスト用ヘルパー


def get_test_env_config() -> Dict[str, str]:
    """テスト用の最小環境設定を返す"""
    return {"DIRSCAN_ROOT_PATH": "/tmp/test_scan", "DIRSCAN_DB_PATH": ":memory:", "DIRSCAN_INMEMORY": "true"}
