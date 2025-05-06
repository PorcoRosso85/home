/**
 * KuzuDBのデータベース接続テスト - 最小構成
 */

import { loadKuzuModule, setupDatabase, closeDatabase } from "./common/db_connection.ts";

async function main() {
  try {
    const kuzu = await loadKuzuModule();
    const { db, conn } = await setupDatabase("test_connection");
    
    const result = await conn.query("RETURN 1 AS test");
    console.log("クエリ結果:", await result.getAllObjects());
    
    await closeDatabase(db, conn);
    console.log("テスト完了");
  } catch (error) {
    console.error("エラー:", error);
    Deno.exit(1);
  }
}

await main();
