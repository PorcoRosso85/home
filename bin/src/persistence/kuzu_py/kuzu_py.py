"""
kuzu_py - KuzuDBの薄いラッパー

KuzuDBのAPIを直接公開しつつ、便利なヘルパー関数を提供
"""
# KuzuDBのAPIを直接公開（APIを隠さない）
try:
    # 必要なAPIのみを明示的にインポート
    import kuzu
    from kuzu import Database, Connection
except ImportError:
    # Nix環境外での開発時のため
    pass

# ヘルパー関数とResult型
from database import create_database, create_connection
from result_types import DatabaseResult, ConnectionResult

# クエリローダー機能
from query_loader import load_typed_query, execute_query
from errors import FileOperationError, ValidationError, NotFoundError

__all__ = [
    # KuzuDBのコアAPI
    "Database",
    "Connection",
    # ヘルパー関数
    "create_database",
    "create_connection",
    # Result型
    "DatabaseResult", 
    "ConnectionResult",
    # エラー型
    "FileOperationError",
    "ValidationError",
    "NotFoundError",
    # クエリローダー
    "load_typed_query",
    "execute_query",
]