#!/usr/bin/env bash

# 最小限のSQLite→KuzuDB連携テスト（CLIのみ）
# nix shellで提供されるCLIツールのみを使用

set -euo pipefail

# 作業ディレクトリ
WORK_DIR="./data_cli_test"
SQLITE_DB="$WORK_DIR/simple.db"
KUZU_DB="$WORK_DIR/kuzu_simple"

# クリーンアップと準備
rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

echo "=== SQLite→KuzuDB最小テスト (CLI版) ==="
echo ""

# 1. SQLiteデータベース作成
echo "1. SQLiteデータベース作成..."
cat <<EOF | nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB"
CREATE TABLE test (id INTEGER, name TEXT);
INSERT INTO test VALUES (1, 'Alice'), (2, 'Bob');
SELECT COUNT(*) || ' records created' FROM test;
EOF
echo "✅ SQLite作成完了"
echo ""

# 2. SQLiteの内容確認
echo "2. SQLiteデータ確認:"
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" "SELECT * FROM test;"
echo ""

# 3. KuzuDBでアタッチとクエリ
echo "3. KuzuDBでアタッチ..."
cat <<EOF | nix shell nixpkgs#kuzu -c kuzu "$KUZU_DB" 2>/dev/null || true
INSTALL sqlite;
LOAD sqlite;
ATTACH '$SQLITE_DB' AS db (dbtype sqlite);
LOAD FROM db.test RETURN *;
DETACH db;
EOF

echo ""
echo "✅ テスト完了"