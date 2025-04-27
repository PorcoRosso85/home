"""
設定変数

このモジュールでは、アプリケーション全体で使用される設定変数を定義します。
CONVENTION.mdに基づき、すべての設定はこのファイルのみで管理されます。
"""

import os

# ルートディレクトリ（ソースコードのルート）
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# データベース関連
DB_PARENT_DIR = os.path.dirname(ROOT_DIR)  # src/kuzu/

# 環境変数からDB_DIRを取得、またはデフォルト値を使用
_db_dir = os.environ.get("KUZU_DB_DIR")
if _db_dir is None:
    _db_dir = os.path.join(DB_PARENT_DIR, "db")  # src/kuzu/db

# グローバル変数として定義（テスト中に書き換えられるように）
DB_DIR = _db_dir
DB_NAME = "DesignKG"

# インメモリモードフラグ（環境変数から取得、デフォルトはFalse）
IN_MEMORY_MODE = os.environ.get("KUZU_IN_MEMORY", "false").lower() == "true"

# クエリ関連
QUERY_DIR = os.path.join(DB_PARENT_DIR, "query")  # src/kuzu/query
QUERY_DML_DIR = os.path.join(QUERY_DIR, "dml")    # src/kuzu/query/dml
QUERY_DDL_DIR = QUERY_DIR                         # src/kuzu/query

# SHACLスキーマ関連
SHAPES_FILE = os.path.join(ROOT_DIR, "design_shapes.ttl")

# DBパスを取得する関数（テスト用オーバーライド用）
def get_db_dir():
    """データベースディレクトリのパスを取得する
    
    テスト中に変数がオーバーライドされた場合、その値を反映
    
    Returns:
        str: データベースディレクトリのパス
    """
    return DB_DIR
