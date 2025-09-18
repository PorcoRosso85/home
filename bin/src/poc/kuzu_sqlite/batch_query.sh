#!/usr/bin/env bash

# SQLiteデータベースに対してバッチでCypherクエリを実行
# 使用方法: ./batch_query.sh <sqlite_db> <cypher_file>

set -euo pipefail

if [ $# -ne 2 ]; then
    echo "使用方法: $0 <sqlite_db> <cypher_file>"
    echo "例: $0 ./data/university.db ./queries/analysis.cypher"
    exit 1
fi

SQLITE_DB="$1"
CYPHER_FILE="$2"

# ファイル存在確認
if [ ! -f "$SQLITE_DB" ]; then
    echo "エラー: SQLiteデータベースが見つかりません: $SQLITE_DB"
    exit 1
fi

if [ ! -f "$CYPHER_FILE" ]; then
    echo "エラー: Cypherファイルが見つかりません: $CYPHER_FILE"
    exit 1
fi

# 一時的なKuzuDBディレクトリ
TEMP_KUZU_DB="/tmp/kuzu_batch_$$"
trap "rm -rf $TEMP_KUZU_DB" EXIT

# バッチ実行用のスクリプト作成
BATCH_SCRIPT="/tmp/batch_$$.cypher"
trap "rm -f $BATCH_SCRIPT" EXIT

cat > "$BATCH_SCRIPT" <<EOF
-- SQLite拡張をロード
INSTALL sqlite;
LOAD sqlite;

-- SQLiteデータベースをアタッチ
ATTACH '$SQLITE_DB' AS db (dbtype sqlite);

-- ユーザー定義のクエリを実行
$(cat "$CYPHER_FILE")

-- デタッチ
DETACH db;
EOF

echo "=== バッチクエリ実行 ==="
echo "SQLiteデータベース: $SQLITE_DB"
echo "Cypherファイル: $CYPHER_FILE"
echo ""

# KuzuDBでバッチ実行
nix shell nixpkgs#kuzu -c kuzu "$TEMP_KUZU_DB" < "$BATCH_SCRIPT"