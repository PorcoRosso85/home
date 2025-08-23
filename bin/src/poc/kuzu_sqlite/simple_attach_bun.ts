#!/usr/bin/env bun

// 簡単なSQLite→KuzuDBアタッチ例（直接実行可能）

import { createDatabase, createConnection } from "../../persistence/kuzu_ts/bun/mod.ts";

async function main() {
  console.log("=== SQLite→KuzuDB簡易アタッチテスト ===\n");

  // SQLiteデータベース準備
  const sqliteDb = "./data_bun/simple.db";
  console.log("1. SQLiteデータベース作成...");
  
  // Bunの組み込みSQLite APIを使用
  const { Database: SQLiteDB } = await import("bun:sqlite");
  const sqlite = new SQLiteDB(sqliteDb, { create: true });
  
  // テーブル作成とデータ投入
  sqlite.run(`
    CREATE TABLE IF NOT EXISTS products (
      id INTEGER PRIMARY KEY,
      name TEXT,
      price REAL
    )
  `);
  
  sqlite.run(`
    INSERT OR REPLACE INTO products (id, name, price) VALUES
    (1, 'Laptop', 999.99),
    (2, 'Mouse', 29.99),
    (3, 'Keyboard', 79.99)
  `);
  
  console.log("✅ SQLiteデータベース準備完了\n");
  
  // KuzuDBでアタッチ
  console.log("2. KuzuDBでアタッチ...");
  
  const dbResult = await createDatabase("./data_bun/kuzu_simple");
  if (!dbResult.success) {
    console.error("❌ KuzuDBデータベース作成失敗:", dbResult.error);
    process.exit(1);
  }
  
  const connResult = await createConnection(dbResult.value);
  if (!connResult.success) {
    console.error("❌ KuzuDB接続作成失敗:", connResult.error);
    process.exit(1);
  }
  
  const conn = connResult.value;
  
  try {
    // SQLite拡張のロード
    await conn.query("INSTALL sqlite;");
    await conn.query("LOAD sqlite;");
    console.log("✅ SQLite拡張ロード完了\n");
    
    // SQLiteデータベースをアタッチ
    await conn.query(`ATTACH '${sqliteDb}' AS shop (dbtype sqlite);`);
    console.log("✅ SQLiteデータベースアタッチ完了\n");
    
    // データ読み込みとCypherクエリ
    console.log("3. データ確認:");
    const result = await conn.query("LOAD FROM shop.products RETURN * ORDER BY price DESC;");
    
    // 結果表示
    console.log("製品一覧（価格順）:");
    while (result.hasNext()) {
      const row = result.getNext();
      console.log(`  - ${row.name}: $${row.price}`);
    }
    
    // 価格でフィルタリング
    console.log("\n50ドル以上の製品:");
    const filtered = await conn.query("LOAD FROM shop.products WHERE price >= 50 RETURN name, price;");
    while (filtered.hasNext()) {
      const row = filtered.getNext();
      console.log(`  - ${row.name}: $${row.price}`);
    }
    
    // デタッチ
    await conn.query("DETACH shop;");
    console.log("\n✅ テスト完了");
    
  } catch (error) {
    console.error("❌ エラー:", error);
    process.exit(1);
  } finally {
    conn.close();
    sqlite.close();
  }
}

// 実行
main().catch(console.error);