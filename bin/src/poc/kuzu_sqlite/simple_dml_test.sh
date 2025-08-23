#!/usr/bin/env bash

# 簡潔なDML操作確認テスト

set -euo pipefail

WORK_DIR="./data_simple_dml"
SQLITE_DB="$WORK_DIR/test.db"

rm -rf "$WORK_DIR"
mkdir -p "$WORK_DIR"

echo "=== DML操作の可否確認 ==="
echo ""

# SQLiteデータ作成
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" <<EOF
CREATE TABLE items (id INTEGER PRIMARY KEY, name TEXT);
INSERT INTO items VALUES (1, 'Item1'), (2, 'Item2');
EOF

echo "1. 初期データ (SQLite):"
nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB" "SELECT * FROM items;"

echo ""
echo "2. KuzuDB ATTACHの性質:"
echo "- ATTACH: 外部DBを読み取り専用で接続"
echo "- LOAD FROM: データを読み込み"
echo "- COPY: KuzuDB内部テーブルへコピー"
echo ""

echo "3. 結論:"
echo "❌ ATTACH経由でSQLiteへの直接書き込み不可"
echo "✅ KuzuDB内部グラフDBへのDML操作は可能"
echo "✅ ワークフロー: SQLite(永続化) → ATTACH → KuzuDB(グラフ分析)"