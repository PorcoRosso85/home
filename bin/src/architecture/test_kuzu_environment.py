#!/usr/bin/env python3
"""
KuzuDB環境の確認スクリプト
"""

import sys
from pathlib import Path

# KuzuDBのインポートを試みる
try:
    import kuzu
    print("✓ KuzuDBがインポートできました")
    print(f"  バージョン: {kuzu.__version__}")
except ImportError as e:
    print("✗ KuzuDBがインポートできません")
    print(f"  エラー: {e}")
    sys.exit(1)

# データベースディレクトリの確認
db_path = Path("/home/nixos/bin/src/architecture/graph_db")
if db_path.exists():
    print(f"✓ データベースディレクトリが存在します: {db_path}")
else:
    print(f"✗ データベースディレクトリが存在しません: {db_path}")

# 接続テスト
try:
    db = kuzu.Database(str(db_path))
    conn = kuzu.Connection(db)
    print("✓ KuzuDBに接続できました")
    
    # テーブル一覧を取得
    result = conn.execute("CALL table_info() RETURN *")
    tables = []
    while result.has_next():
        row = result.get_next()
        tables.append(row)
    
    if tables:
        print(f"✓ 既存のテーブル数: {len(tables)}")
        for table in tables:
            print(f"  - {table}")
    else:
        print("  既存のテーブルはありません")
    
    conn.close()
    
except Exception as e:
    print(f"✗ KuzuDB接続エラー: {e}")
    sys.exit(1)

print("\nKuzuDB環境は正常です。")