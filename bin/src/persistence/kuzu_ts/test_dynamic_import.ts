/**
 * 動的import検証テスト
 */

// kuzu/queryの実装を参考に動的importをテスト
async function testDynamicImport() {
  console.log("=== Dynamic Import Test ===");
  
  try {
    // 動的import
    const kuzu = await import("npm:kuzu");
    console.log("✅ Dynamic import successful");
    console.log("Available exports:", Object.keys(kuzu));
    
    // インメモリデータベース作成
    const db = new kuzu.Database(":memory:");
    console.log("✅ Database created");
    
    // コネクション作成
    const conn = new kuzu.Connection(db);
    console.log("✅ Connection created");
    
    // テーブル作成
    await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
    console.log("✅ Table created");
    
    // データ挿入
    await conn.query("CREATE (p:Person {name: 'Alice', age: 30})");
    await conn.query("CREATE (p:Person {name: 'Bob', age: 25})");
    console.log("✅ Data inserted");
    
    // クエリ実行
    const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
    const rows = await result.getAll();
    console.log("✅ Query executed");
    console.log("Results:", rows);
    
    // 明示的なクリーンアップ
    await conn.close();
    console.log("✅ Connection closed");
    
    await db.close();
    console.log("✅ Database closed");
    
    console.log("\n🎉 All tests passed without panic!");
    
  } catch (error) {
    console.error("❌ Error:", error);
  }
}

// メイン実行
if (import.meta.main) {
  await testDynamicImport();
  
  // 少し待機してからプロセス終了
  console.log("\nWaiting for cleanup...");
  await new Promise(resolve => setTimeout(resolve, 1000));
  console.log("Done!");
}