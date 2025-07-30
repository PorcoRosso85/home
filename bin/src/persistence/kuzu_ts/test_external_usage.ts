/**
 * 外部からの使用可能性テスト
 * Worker実装が外部モジュールとして利用できるかを確認
 */

// mod_worker.tsから直接インポート（外部利用を想定）
import { 
  createDatabase, 
  createConnection,
  terminateWorker,
  isDatabase,
  isConnection,
  isValidationError
} from "./mod_worker.ts";

async function testExternalUsage() {
  console.log("=== External Usage Test ===");
  
  try {
    // 1. データベース作成
    console.log("1. Creating database...");
    const dbResult = await createDatabase(":memory:");
    
    if (isValidationError(dbResult)) {
      console.error("Failed to create database:", dbResult);
      return;
    }
    
    console.log("✅ Database created successfully");
    
    // 2. コネクション作成
    console.log("\n2. Creating connection...");
    const connResult = await createConnection(dbResult);
    
    if (isValidationError(connResult)) {
      console.error("Failed to create connection:", connResult);
      return;
    }
    
    console.log("✅ Connection created successfully");
    
    // 3. 基本的なクエリ実行
    console.log("\n3. Executing queries...");
    
    // テーブル作成
    await connResult.query("CREATE NODE TABLE Person(id INT64, name STRING, PRIMARY KEY(id))");
    console.log("✅ Table created");
    
    // データ挿入
    await connResult.query("CREATE (p:Person {id: 1, name: 'Alice'})");
    await connResult.query("CREATE (p:Person {id: 2, name: 'Bob'})");
    console.log("✅ Data inserted");
    
    // データ取得
    const result = await connResult.query("MATCH (p:Person) RETURN p.id, p.name ORDER BY p.id");
    const rows = await result.getAll();
    console.log("✅ Query executed");
    console.log("Results:", rows);
    
    // 4. クリーンアップ
    console.log("\n4. Cleaning up...");
    await connResult.close();
    await dbResult.close();
    console.log("✅ Resources cleaned up");
    
    // 5. ワーカー終了
    console.log("\n5. Terminating worker...");
    terminateWorker();
    console.log("✅ Worker terminated");
    
    console.log("\n🎉 External usage test PASSED!");
    console.log("The Worker implementation can be used as an external module.");
    
  } catch (error) {
    console.error("❌ Test failed:", error);
  }
}

// 実行
if (import.meta.main) {
  await testExternalUsage();
}