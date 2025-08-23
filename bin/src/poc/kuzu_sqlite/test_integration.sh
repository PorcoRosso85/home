#!/usr/bin/env bash

# 統合テスト：SQLite→KuzuDB連携の動作確認
# POCの仕様を検証する実行可能なテスト

set -euo pipefail

# テスト用の一時ディレクトリ
TEST_DIR="/tmp/kuzu_sqlite_test_$$"
trap "rm -rf $TEST_DIR" EXIT

echo "=== 統合テスト開始 ==="
mkdir -p "$TEST_DIR"
cd "$TEST_DIR"

# テスト1: SQLiteデータベース作成
echo "Test 1: SQLiteデータベース作成..."
cat <<EOF | nix shell nixpkgs#sqlite -c sqlite3 test.db
CREATE TABLE person (name TEXT PRIMARY KEY, age INTEGER);
INSERT INTO person VALUES ('Alice', 30), ('Bob', 25);
EOF

# 作成確認
RESULT=$(nix shell nixpkgs#sqlite -c sqlite3 test.db "SELECT COUNT(*) FROM person;")
if [ "$RESULT" = "2" ]; then
    echo "✅ SQLiteデータベース作成成功"
else
    echo "❌ SQLiteデータベース作成失敗"
    exit 1
fi

# テスト2: KuzuDBでのアタッチとクエリ
echo ""
echo "Test 2: KuzuDBアタッチとクエリ実行..."
KUZU_RESULT=$(cat <<EOF | nix shell nixpkgs#kuzu -c kuzu kuzu_test_db 2>/dev/null | grep -c "Alice\|Bob" || true
INSTALL sqlite;
LOAD sqlite;
ATTACH 'test.db' AS testdb (dbtype sqlite);
LOAD FROM testdb.person RETURN name;
EOF
)

if [ "$KUZU_RESULT" -ge "2" ]; then
    echo "✅ KuzuDBアタッチ成功"
else
    echo "❌ KuzuDBアタッチ失敗"
    exit 1
fi

# テスト3: Cypherクエリでのフィルタリング
echo ""
echo "Test 3: Cypherクエリでのフィルタリング..."
FILTER_RESULT=$(cat <<EOF | nix shell nixpkgs#kuzu -c kuzu kuzu_test_db2 2>/dev/null | grep -c "Alice" || true
INSTALL sqlite;
LOAD sqlite;
ATTACH 'test.db' AS testdb (dbtype sqlite);
LOAD FROM testdb.person WHERE age > 28 RETURN name;
EOF
)

if [ "$FILTER_RESULT" -eq "1" ]; then
    echo "✅ フィルタリング成功"
else
    echo "❌ フィルタリング失敗"
    exit 1
fi

echo ""
echo "=== すべてのテスト成功 ✅ ==="
echo ""
echo "仕様確認完了:"
echo "- SQLite永続化機能: 動作確認済み"
echo "- KuzuDBアタッチ機能: 動作確認済み"
echo "- Cypherクエリ実行: 動作確認済み"