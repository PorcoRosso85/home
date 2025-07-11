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

def get_rgl_database_path() -> str:
    """RGL_DATABASE_PATH（必須）
    
    Returns:
        str: データベースパス（':memory:' または実際のパス）
        
    Raises:
        EnvironmentError: RGL_DATABASE_PATH未設定の場合
    """
    return _require_env('RGL_DATABASE_PATH')

def get_db_path() -> str:
    """DBパスを取得（/orgモード対応、後方互換性）
    
    Returns:
        str: データベースパス
    """
    # 新しい環境変数を優先
    try:
        return get_rgl_database_path()
    except EnvironmentError:
        # 後方互換性（一時的）
        try:
            return _require_env('RGL_DB_PATH')
        except EnvironmentError:
            raise EnvironmentError(
                "RGL_DATABASE_PATH not set. "
                "Set RGL_DATABASE_PATH=:memory: for in-memory DB, "
                "or RGL_DATABASE_PATH=/path/to/db for persistent DB"
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
    if not os.environ.get('RGL_DATABASE_PATH') and not os.environ.get('RGL_DB_PATH'):
        errors['RGL_DATABASE_PATH'] = (
            "RGL_DATABASE_PATH not set. "
            "Set RGL_DATABASE_PATH=:memory: for in-memory DB, "
            "or RGL_DATABASE_PATH=/path/to/db for persistent DB"
        )

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
