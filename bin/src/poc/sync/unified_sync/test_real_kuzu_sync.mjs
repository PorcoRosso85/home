/**
 * Real KuzuDB WASM Test (Sync Build) - モック禁止
 * 同期版ビルドを使用（Worker不要）
 */

import kuzu from "kuzu-wasm/sync";

// 同期版ビルドでKuzuDB WASMを使用
async function testRealKuzuWASM() {
  // 同期版も初期化が必要
  await kuzu.init();
  
  // Database作成
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);
  
  // スキーマ作成
  conn.query(`
    CREATE NODE TABLE User(
      id STRING, 
      name STRING, 
      PRIMARY KEY(id)
    )
  `);
  
  // データ挿入
  conn.query(`
    CREATE (u:User {id: 'u1', name: 'Alice'})
  `);
  
  // クエリ実行
  const result = conn.query(`
    MATCH (u:User)
    RETURN u.id as id, u.name as name
  `);
  
  // 結果取得（同期版）
  const users = result.getAllObjects();
  
  // 検証
  if (!users || users.length !== 1) {
    throw new Error(`Expected 1 user, got ${users ? users.length : 'undefined'}`);
  }
  if (users[0].id !== 'u1') {
    throw new Error(`Expected id 'u1', got '${users[0].id}'`);
  }
  if (users[0].name !== 'Alice') {
    throw new Error(`Expected name 'Alice', got '${users[0].name}'`);
  }
  
  console.log("✅ Real KuzuDB WASM (sync build) test passed!");
  console.log("  - User created:", users[0]);
}

// 実行
testRealKuzuWASM().catch(console.error);