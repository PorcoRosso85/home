"""
テスト環境用の環境変数管理
依存: env.py
外部依存: なし

テスト実行時に必要な環境変数の設定を提供します。
本番環境の規約（デフォルト値禁止）を守りつつ、
テストに必要な最小限の設定を提供します。
"""
import os
from typing import Dict

def setup_test_environment() -> None:
    """テスト用の環境変数を設定

    既に設定されている環境変数は上書きしません。
    """
    # 必須環境変数のデフォルト値（テスト用）
    test_defaults = {
        'RGL_DB_PATH': '/tmp/test_rgl_db',
        'RGL_SKIP_SCHEMA_CHECK': 'true',  # テスト時はスキーマチェックをスキップ
    }

    for key, value in test_defaults.items():
        if key not in os.environ:
            os.environ[key] = value

def get_test_db_path() -> str:
    """テスト用のデータベースパスを取得

    Returns:
        str: テスト用DBパス
    """
    return os.environ.get('RGL_TEST_DB_PATH', '/tmp/test_rgl_db')

def enable_test_mode() -> None:
    """テストモードを有効化

    スキーマチェックをスキップし、テスト用の設定を適用します。
    """
    os.environ['RGL_SKIP_SCHEMA_CHECK'] = 'true'

def disable_test_mode() -> None:
    """テストモードを無効化

    テスト用の設定をクリアします。
    """
    if 'RGL_SKIP_SCHEMA_CHECK' in os.environ:
        del os.environ['RGL_SKIP_SCHEMA_CHECK']

def with_test_env(**kwargs) -> Dict[str, str]:
    """テスト用の環境変数を一時的に設定するためのコンテキスト用辞書を作成

    Args:
        **kwargs: 設定する環境変数

    Returns:
        Dict[str, str]: 元の環境変数の値

    Example:
        >>> original = with_test_env(RGL_HIERARCHY_MODE='dynamic')
        >>> # テスト実行
        >>> restore_env(original)
    """
    original = {}
    for key, value in kwargs.items():
        original[key] = os.environ.get(key)
        os.environ[key] = value
    return original

def restore_env(original: Dict[str, str]) -> None:
    """環境変数を元に戻す

    Args:
        original: with_test_envで取得した元の値
    """
    for key, value in original.items():
        if value is None:
            if key in os.environ:
                del os.environ[key]
        else:
            os.environ[key] = value
