"""
データベースファクトリー - persistence.kuzuへのプロキシ

このモジュールは後方互換性のために残されています。
新しいコードではpersistence.kuzu.core.databaseを直接使用してください。
"""
import os
import sys

# PYTHONPATHにbin/srcを追加（必要な場合）
bin_src_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../"))
if bin_src_path not in sys.path:
    sys.path.insert(0, bin_src_path)

# persistence.kuzuの関数をインポートして再エクスポート
from persistence.kuzu.core.database import (
    create_database,
    create_connection,
    clear_database_cache,
    clear_cache
)

# 後方互換性のため、すべての関数を公開
__all__ = [
    'create_database',
    'create_connection', 
    'clear_database_cache',
    'clear_cache'
]