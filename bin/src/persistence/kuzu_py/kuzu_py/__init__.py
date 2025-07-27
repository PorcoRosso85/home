"""
kuzu_py - KuzuDBの薄いラッパー

KuzuDBのAPIを直接公開しつつ、便利なヘルパー関数を提供
"""
# KuzuDBのAPIを直接公開（APIを隠さない）
try:
    # シンプルにkuzuをインポート
    import kuzu
    from kuzu import *
except ImportError:
    # Nix環境外での開発時のため
    pass

# ヘルパー関数とResult型
from .database import create_database, create_connection
from .result_types import DatabaseResult, ConnectionResult, ErrorDict

# クエリローダー機能（実験的）
from .query_loader import load_query_from_file, clear_query_cache

__all__ = [
    # ヘルパー関数
    "create_database",
    "create_connection",
    # Result型
    "DatabaseResult", 
    "ConnectionResult",
    "ErrorDict",
    # クエリローダー（実験的）
    "load_query_from_file",
    "clear_query_cache",
]