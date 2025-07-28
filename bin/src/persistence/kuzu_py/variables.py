"""
環境変数とグローバル設定

規約準拠:
- module_design.md: 環境変数の一元管理
- error_handling.md: 設定エラーの適切な処理
"""
import os
from pathlib import Path
from typing import Optional, Union
from result_types import ErrorDict


def get_kuzu_path() -> Union[str, ErrorDict]:
    """
    KuzuDBのパスを環境変数から取得
    
    Returns:
        成功時: パス文字列
        失敗時: ErrorDict
    """
    path = os.environ.get("KUZU_DB_PATH")
    if path is None:
        # デフォルトパスを使用
        return str(Path.home() / ".kuzu" / "default.db")
    
    return path


def get_cache_enabled() -> bool:
    """
    クエリキャッシュが有効かどうかを環境変数から取得
    
    Returns:
        キャッシュ有効フラグ（デフォルト: True）
    """
    cache_enabled = os.environ.get("KUZU_PY_CACHE_ENABLED", "true")
    return cache_enabled.lower() in ["true", "1", "yes", "on"]


def get_max_cache_size() -> int:
    """
    クエリキャッシュの最大サイズを取得
    
    Returns:
        最大キャッシュサイズ（デフォルト: 100）
    """
    try:
        return int(os.environ.get("KUZU_PY_MAX_CACHE_SIZE", "100"))
    except ValueError:
        return 100


def get_debug_mode() -> bool:
    """
    デバッグモードが有効かどうかを取得
    
    Returns:
        デバッグモードフラグ（デフォルト: False）
    """
    debug = os.environ.get("KUZU_PY_DEBUG", "false")
    return debug.lower() in ["true", "1", "yes", "on"]


# グローバル定数
DEFAULT_DB_MAX_SIZE = 1 << 30  # 1GB
DEFAULT_CACHE_TTL = 3600  # 1時間（秒）

# サポートされるクエリタイプ
VALID_QUERY_TYPES = ["dml", "dql", "auto"]

# ファイル拡張子
QUERY_FILE_EXTENSION = ".cypher"

# デフォルトクエリディレクトリ
DEFAULT_QUERY_DIR = "./queries"