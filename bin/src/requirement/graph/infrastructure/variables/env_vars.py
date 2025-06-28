"""
環境変数管理モジュール

すべての環境変数へのアクセスを一元化します。
必須環境変数はエラーを発生させ、オプション環境変数はデフォルト値を提供します。
"""
import os
import json
from typing import Optional, Dict, List

# 必須環境変数チェック
def _check_env(name: str) -> str:
    """環境変数の存在を確認し、なければエラー"""
    value = os.environ.get(name)
    if not value:
        raise EnvironmentError(
            f"{name} not set. "
            f"Run with: {name}=<value> ... python ..."
        )
    return value

# 必須環境変数
LD_LIBRARY_PATH = _check_env('LD_LIBRARY_PATH')
RGL_DB_PATH = _check_env('RGL_DB_PATH')

# オプション環境変数（デフォルト値付き）
# 注意: 動的に読み込むため、module-levelでキャッシュしない
RGL_LOG_LEVEL = os.environ.get('RGL_LOG_LEVEL', '*:WARN')
RGL_LOG_FORMAT = os.environ.get('RGL_LOG_FORMAT', 'console')
RGL_SKIP_SCHEMA_CHECK = os.environ.get('RGL_SKIP_SCHEMA_CHECK', 'false')

# アクセス関数
def get_db_path() -> str:
    """DBパスを取得"""
    return RGL_DB_PATH

def get_log_level() -> str:
    """ログレベルを取得"""
    return os.environ.get('RGL_LOG_LEVEL', '*:WARN')

def get_log_format() -> str:
    """ログフォーマットを取得"""
    return os.environ.get('RGL_LOG_FORMAT', 'console')

def get_hierarchy_mode() -> str:
    """階層モードを取得（動的読み込み）"""
    return os.environ.get('RGL_HIERARCHY_MODE', 'legacy')

def get_max_hierarchy() -> int:
    """最大階層深度を取得（動的読み込み）"""
    return int(os.environ.get('RGL_MAX_HIERARCHY', '5'))

def get_team() -> str:
    """チーム設定を取得（動的読み込み）"""
    return os.environ.get('RGL_TEAM', 'product')

def get_hierarchy_keywords() -> Optional[Dict[int, List[str]]]:
    """階層キーワード定義を取得（環境変数から）"""
    keywords_str = os.environ.get('RGL_HIERARCHY_KEYWORDS', None)
    if keywords_str:
        try:
            # キーを整数に変換
            raw_dict = json.loads(keywords_str)
            return {int(k): v for k, v in raw_dict.items()}
        except (json.JSONDecodeError, ValueError):
            return None
    return None

def should_skip_schema_check() -> bool:
    """スキーマチェックをスキップするかどうか"""
    skip_check = os.environ.get('RGL_SKIP_SCHEMA_CHECK', 'false')
    return skip_check.lower() in ('true', '1', 'yes', 'on')