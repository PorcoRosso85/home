#!/usr/bin/env bash

# 既存のSQLiteデータベースに対してKuzuDBでクエリを実行する簡単な例
# 使用方法: ./simple_query.sh <sqlite_db_path>

set -euo pipefail

# 引数チェック
if [ $# -ne 1 ]; then
    echo "使用方法: $0 <sqlite_db_path>"
    echo "例: $0 ./data/university.db"
    exit 1
fi

SQLITE_DB="$1"

# SQLiteデータベースの存在確認
if [ ! -f "$SQLITE_DB" ]; then
    echo "エラー: SQLiteデータベースが見つかりません: $SQLITE_DB"
    exit 1
fi

# 一時的なKuzuDBディレクトリ
TEMP_KUZU_DB="/tmp/kuzu_temp_$$"
trap "rm -rf $TEMP_KUZU_DB" EXIT

echo "=== SQLiteデータベースをKuzuDBでクエリ実行 ==="
echo "SQLiteデータベース: $SQLITE_DB"
echo ""

# インタラクティブなクエリ実行
cat <<EOF
利用可能なコマンド例:
  INSTALL sqlite;
  LOAD sqlite;
  ATTACH '$SQLITE_DB' AS db (dbtype sqlite);
  SHOW TABLES;
  LOAD FROM db.<table_name> RETURN *;
  DETACH db;

Ctrl+D または .quit で終了
EOF

echo ""
nix shell nixpkgs#kuzu -c kuzu "$TEMP_KUZU_DB"