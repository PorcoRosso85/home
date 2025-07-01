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
import sys
from typing import Optional, Dict, List
import json

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

def get_ld_library_path() -> str:
    """LD_LIBRARY_PATH（必須）"""
    return _require_env('LD_LIBRARY_PATH')

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

def get_hierarchy_mode() -> Optional[str]:
    """階層モード（オプション）"""
    return _optional_env('RGL_HIERARCHY_MODE')

def get_max_hierarchy() -> Optional[int]:
    """最大階層深度（オプション）"""
    value = _optional_env('RGL_MAX_HIERARCHY')
    if value:
        try:
            return int(value)
        except ValueError:
            raise EnvironmentError(f"RGL_MAX_HIERARCHY must be an integer, got: {value}")
    return None

def get_team() -> Optional[str]:
    """チーム名（オプション）"""
    return _optional_env('RGL_TEAM')

def get_hierarchy_keywords() -> Optional[Dict[int, List[str]]]:
    """階層キーワード（オプション）"""
    value = _optional_env('RGL_HIERARCHY_KEYWORDS')
    if value:
        try:
            return json.loads(value)
        except json.JSONDecodeError as e:
            raise EnvironmentError(f"RGL_HIERARCHY_KEYWORDS must be valid JSON: {e}")
    return None

# /org モード関連

def is_org_mode() -> bool:
    """/orgモードが有効か"""
    mode = _optional_env('RGL_ORG_MODE')
    return mode and mode.lower() == 'true'

def get_shared_db_path() -> Optional[str]:
    """共有DBパス（/orgモード用）"""
    return _optional_env('RGL_SHARED_DB_PATH')

# パス関連（環境変数ベース）

def get_kuzu_module_path() -> Optional[str]:
    """KuzuDBモジュールパス（環境変数またはフォールバック）"""
    # 環境変数から取得
    env_path = _optional_env('RGL_KUZU_MODULE_PATH')
    if env_path:
        return env_path
    
    # フォールバックパスを試す
    fallback_paths = [
        "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu",
        "/home/nixos/bin/src/requirement/graph/.venv/lib/python3.11/site-packages/kuzu",
        ".venv/lib/python3.11/site-packages/kuzu",
        "../.venv/lib/python3.11/site-packages/kuzu",
    ]
    
    for path in fallback_paths:
        if os.path.exists(path) and os.path.exists(os.path.join(path, "__init__.py")):
            return path
    
    # 動的に検出を試みる
    try:
        import kuzu
        if hasattr(kuzu, '__file__') and kuzu.__file__:
            return os.path.dirname(kuzu.__file__)
    except ImportError:
        pass
    
    return None

# 設定検証

def validate_environment() -> Dict[str, str]:
    """環境設定を検証し、問題があればエラー詳細を返す"""
    errors = {}
    
    # 必須環境変数チェック
    required = ['LD_LIBRARY_PATH', 'RGL_DB_PATH']
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
        'LD_LIBRARY_PATH': '/test/lib',
        'RGL_DB_PATH': '/test/db'
    }