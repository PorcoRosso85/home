"""
環境変数管理 - 外部設定の一元管理
依存: なし
外部依存: なし

規約遵守:
- デフォルト値禁止
- 必須環境変数は明示的にエラー
- 関数として提供（グローバル状態禁止）
"""
import os
from typing import Optional, Dict

# エラー型定義
class EnvironmentError(Exception):
    """環境変数関連エラー"""
    pass

# 必須環境変数チェック
def _require_env(name: str) -> str:
    """必須環境変数を取得（デフォルト値なし）"""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"{name} not set. Set {name}=<value> before running the application"
        )
    return value

# オプション環境変数取得
def _optional_env(name: str) -> Optional[str]:
    """オプション環境変数を取得"""
    return os.environ.get(name)

# 環境変数アクセス関数

def get_ld_library_path() -> Optional[str]:
    """LD_LIBRARY_PATH（オプション - Nixが管理）"""
    return _optional_env('LD_LIBRARY_PATH')

def get_rgl_db_path() -> str:
    """RGL_DB_PATH（必須）"""
    return _require_env('RGL_DB_PATH')

def get_db_path() -> str:
    """DBパスを取得（/orgモード対応）"""
    # /orgモードで共有DBが設定されている場合はそちらを優先
    org_mode = _optional_env('RGL_ORG_MODE')
    shared_db = _optional_env('RGL_SHARED_DB_PATH')

    if org_mode and org_mode.lower() == 'true' and shared_db:
        return shared_db
    return get_rgl_db_path()

def get_log_level() -> Optional[str]:
    """ログレベル（オプション）"""
    return _optional_env('RGL_LOG_LEVEL')

def get_log_format() -> Optional[str]:
    """ログフォーマット（オプション）"""
    return _optional_env('RGL_LOG_FORMAT')

def should_skip_schema_check() -> bool:
    """スキーマチェックをスキップするか"""
    value = _optional_env('RGL_SKIP_SCHEMA_CHECK')
    return value and value.lower() in ('true', '1', 'yes')

# 階層関連の環境変数は hierarchy_env.py に移動

# /org モード関連

def is_org_mode() -> bool:
    """/orgモードが有効か"""
    mode = _optional_env('RGL_ORG_MODE')
    return mode and mode.lower() == 'true'

def get_shared_db_path() -> Optional[str]:
    """共有DBパス（/orgモード用）"""
    return _optional_env('RGL_SHARED_DB_PATH')

# パス関連は削除（環境設定で解決）

# 設定検証

def validate_environment() -> Dict[str, str]:
    """環境設定を検証し、問題があればエラー詳細を返す"""
    errors = {}

    # 必須環境変数チェック（LD_LIBRARY_PATHは削除 - Nixが管理）
    required = ['RGL_DB_PATH']
    for var in required:
        if not os.environ.get(var):
            errors[var] = f"Required environment variable {var} is not set"

    # /orgモード設定の整合性チェック
    if is_org_mode() and not get_shared_db_path():
        errors['RGL_SHARED_DB_PATH'] = "RGL_SHARED_DB_PATH must be set when RGL_ORG_MODE=true"

    return errors

# テスト用ヘルパー

def get_test_env_config() -> Dict[str, str]:
    """テスト用の最小環境設定を返す"""
    return {
        'RGL_DB_PATH': '/test/db'
    }
