"""
パス関連定義モジュール

ファイルパスやモジュールパスの定義を管理します。
"""
import os
from typing import Optional

# KuzuDBモジュールパス（動的に検出）
def get_kuzu_module_path() -> Optional[str]:
    """KuzuDBモジュールのパスを動的に検出"""
    try:
        import kuzu
        if hasattr(kuzu, '__file__') and kuzu.__file__:
            return os.path.dirname(kuzu.__file__)
        else:
            # Built-in module or C extension without __file__
            return None
    except ImportError:
        # フォールバック（既知のパス）
        fallback_path = "/home/nixos/bin/src/.venv/lib/python3.11/site-packages/kuzu"
        if os.path.exists(fallback_path):
            return fallback_path
        return None

# デフォルトパス定義
DEFAULT_DB_PATH = "~/.rgl/graph.db"
DEFAULT_JSONL_PATH = "~/.rgl/decisions.jsonl"

def get_default_kuzu_db_path() -> str:
    """デフォルトのKuzuDBパスを取得（展開済み）"""
    return os.path.expanduser(DEFAULT_DB_PATH)

def get_default_jsonl_path() -> str:
    """デフォルトのJSONLパスを取得（展開済み）"""
    return os.path.expanduser(DEFAULT_JSONL_PATH)
