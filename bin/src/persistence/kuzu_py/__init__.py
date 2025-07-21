"""
kuzu_py - KuzuDBの薄いラッパー

KuzuDBのAPIを直接公開しつつ、便利なヘルパー関数を提供
"""
# KuzuDBのAPIを直接公開（APIを隠さない）
try:
    from kuzu import *
except ImportError:
    # Nix環境外での開発時のため
    pass

# ヘルパー関数とResult型
from .database import create_database, create_connection
from .result_types import DatabaseResult, ConnectionResult, ErrorDict

__all__ = [
    # ヘルパー関数
    "create_database",
    "create_connection",
    # Result型
    "DatabaseResult", 
    "ConnectionResult",
    "ErrorDict",
]