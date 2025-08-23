#!/usr/bin/env bash

# 最小限のSQLite→KuzuDB連携確認（Bun版）
# KuzuDB TSライブラリを使用したアタッチ動作確認

set -euo pipefail

# 作業ディレクトリ
WORK_DIR="./data_bun"
SQLITE_DB="$WORK_DIR/test.db"

# ディレクトリ作成
mkdir -p "$WORK_DIR"

echo "=== 最小限のSQLite→KuzuDB連携テスト (Bun版) ==="
echo ""

# 1. SQLiteデータベース作成
echo "1. SQLiteデータベース作成..."
cat <<EOF | nix shell nixpkgs#sqlite -c sqlite3 "$SQLITE_DB"
CREATE TABLE users (id INTEGER PRIMARY KEY, name TEXT);
INSERT INTO users (id, name) VALUES (1, 'Alice'), (2, 'Bob');
EOF
echo "✅ SQLiteデータベース作成完了"

# 2. Bunスクリプト作成
echo ""
echo "2. Bunスクリプト作成..."
cat > "$WORK_DIR/attach_test.ts" <<'EOF'
// SQLiteをKuzuDBにアタッチする最小例
// 実際のパスを使用
const kuzuPath = "../../../persistence/kuzu_ts/bun/simple_wrapper.ts";
const { createKuzuDatabase, executeQuery } = await import(kuzuPath);

async function main() {
  console.log("KuzuDB接続開始...");
  
  try {
    // KuzuDBデータベース作成
    const db = new Database("./kuzu_db");
    const conn = new Connection(db);
    
    // SQLite拡張をインストール・ロード
    await conn.query("INSTALL sqlite;");
    await conn.query("LOAD sqlite;");
    console.log("✅ SQLite拡張ロード完了");
    
    // SQLiteデータベースをアタッチ
    await conn.query("ATTACH './test.db' AS sqlitedb (dbtype sqlite);");
    console.log("✅ SQLiteデータベースアタッチ完了");
    
    // データ確認
    const result = await conn.query("LOAD FROM sqlitedb.users RETURN *;");
    console.log("✅ データ読み込み成功:");
    
    // 結果表示
    while (result.hasNext()) {
      const row = result.getNext();
      console.log(`  ID: ${row.id}, Name: ${row.name}`);
    }
    
    // クリーンアップ
    await conn.query("DETACH sqlitedb;");
    conn.close();
    
    console.log("✅ テスト完了");
  } catch (error) {
    console.error("❌ エラー:", error);
    process.exit(1);
  }
}

main();
EOF
echo "✅ Bunスクリプト作成完了"

# 3. Bunで実行
echo ""
echo "3. Bunスクリプト実行..."
cd "$WORK_DIR"
nix shell nixpkgs#bun -c bun run attach_test.ts

echo ""
echo "=== 最小限テスト完了 ==="