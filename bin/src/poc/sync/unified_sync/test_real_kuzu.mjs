/**
 * Real KuzuDB WASM Test - モック禁止
 * Node.js環境で実際のKuzuDB WASMを使用するテスト
 */

import { createRequire } from 'module';

// Node.js環境でKuzuDB WASM nodejsビルドを使用
async function testRealKuzuWASM() {
  // CommonJSモジュールをESMから読み込む
  const require = createRequire(import.meta.url);
  const kuzu = require("kuzu-wasm/nodejs");
  
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
  
  // デバッグ情報追加
  console.log("Result:", result);
  console.log("Result type:", typeof result);
  console.log("Result methods:", Object.getOwnPropertyNames(Object.getPrototypeOf(result)));
  
  const users = result.getAllObjects ? result.getAllObjects() : [];
  console.log("Users:", users);
  
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
  
  console.log("✅ Real KuzuDB WASM test passed!");
}

// 実行
testRealKuzuWASM().catch(console.error);