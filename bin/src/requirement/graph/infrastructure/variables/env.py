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
from typing import Optional, Dict, Union
from domain.errors import EnvironmentConfigError

# 必須環境変数チェック
def _require_env(name: str) -> Union[str, EnvironmentConfigError]:
    """必須環境変数を取得（エラー値を返す）"""
    value = os.environ.get(name)
    if not value:
        return EnvironmentConfigError(
            type="EnvironmentConfigError",
            message=f"{name} not set. Set {name}=<value> before running the application",
            variable=name,
            current_value=None,
            expected_format="Non-empty string"
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

def get_rgl_database_path() -> Union[str, EnvironmentConfigError]:
    """RGL_DATABASE_PATH（必須）
    
    Returns:
        Union[str, EnvironmentConfigError]: データベースパスまたはエラー
    """
    return _require_env('RGL_DATABASE_PATH')

def get_db_path() -> Union[str, EnvironmentConfigError]:
    """DBパスを取得（/orgモード対応）
    
    Returns:
        Union[str, EnvironmentConfigError]: データベースパスまたはエラー
    """
    # 新しい環境変数を優先
    result = get_rgl_database_path()
    if not (isinstance(result, dict) and result.get("type") == "EnvironmentConfigError"):
        return result
    
    # 後方互換性チェック
    legacy_result = _require_env('RGL_DB_PATH')
    if not (isinstance(legacy_result, dict) and legacy_result.get("type") == "EnvironmentConfigError"):
        return legacy_result
    
    return EnvironmentConfigError(
        type="EnvironmentConfigError",
        message="RGL_DATABASE_PATH not set. Set RGL_DATABASE_PATH=:memory: for in-memory DB, or RGL_DATABASE_PATH=/path/to/db for persistent DB",
        variable="RGL_DATABASE_PATH",
        current_value=None,
        expected_format="':memory:' or '/path/to/db'"
    )

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

    # 必須環境変数チェック
    db_path = get_db_path()
    if isinstance(db_path, dict) and db_path.get("type") == "EnvironmentConfigError":
        errors['RGL_DATABASE_PATH'] = db_path["message"]

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
