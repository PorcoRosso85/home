/**
 * Real KuzuDB WASM Test - モック禁止
 * Node.js環境で実際のKuzuDB WASMを使用するテスト
 */

// Node.js環境でKuzuDB WASM nodejsビルドを使用
async function testRealKuzuWASM() {
  // Node.js版をインポート（CommonJS）
  const kuzu = await import("kuzu-wasm/nodejs");
  
  // 初期化
  await kuzu.default.init();
  
  // Database作成
  const db = new kuzu.default.Database(':memory:');
  const conn = new kuzu.default.Connection(db);
  
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
  
  const users = result.getAllObjects();
  
  // 検証
  if (users.length !== 1) {
    throw new Error(`Expected 1 user, got ${users.length}`);
  }
  if (users[0].id !== 'u1') {
    throw new Error(`Expected id 'u1', got '${users[0].id}'`);
  }
  if (users[0].name !== 'Alice') {
    throw new Error(`Expected name 'Alice', got '${users[0].name}'`);
  }
  
  console.log("✅ Real KuzuDB WASM test passed!");
}

// Node.js環境でのみ実行
if (typeof process !== 'undefined' && process.versions && process.versions.node) {
  testRealKuzuWASM().catch(console.error);
} else {
  console.log("⚠️ This test requires Node.js environment");
}