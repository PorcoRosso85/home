/**
 * Real KuzuDB WASM Test (Default Build) - モック禁止
 * ブラウザ/Node.js両対応のデフォルトビルドを使用
 */

import kuzu from "kuzu-wasm";

// デフォルトビルドでKuzuDB WASMを使用
async function testRealKuzuWASM() {
  // 初期化
  await kuzu.init();
  
  // Database作成
  const db = new kuzu.Database(':memory:');
  const conn = new kuzu.Connection(db);
  
  // スキーマ作成
  await conn.query(`
    CREATE NODE TABLE User(
      id STRING, 
      name STRING, 
      PRIMARY KEY(id)
    )
  `);
  
  // データ挿入
  await conn.query(`
    CREATE (u:User {id: 'u1', name: 'Alice'})
  `);
  
  // クエリ実行
  const result = await conn.query(`
    MATCH (u:User)
    RETURN u.id as id, u.name as name
  `);
  
  // 結果取得
  const users = await result.getAllObjects();
  
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
  
  console.log("✅ Real KuzuDB WASM (default build) test passed!");
  console.log("  - User created:", users[0]);
}

// 実行
testRealKuzuWASM().catch(console.error);