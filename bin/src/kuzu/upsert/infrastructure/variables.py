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
DB_DIR = os.path.join(DB_PARENT_DIR, "db")  # src/kuzu/db
DB_NAME = "DesignKG"

# クエリ関連
QUERY_DIR = os.path.join(DB_PARENT_DIR, "query")  # src/kuzu/query
QUERY_DML_DIR = os.path.join(QUERY_DIR, "dml")    # src/kuzu/query/dml
QUERY_DDL_DIR = QUERY_DIR                         # src/kuzu/query

# SHACLスキーマ関連
SHAPES_FILE = os.path.join(ROOT_DIR, "design_shapes.ttl")
