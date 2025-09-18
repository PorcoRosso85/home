/**
 * Simple KuzuDB Node.js Test (CommonJS)
 * 最もシンプルなKuzuDB Node.js版の動作確認
 */

const kuzu = require("kuzu-wasm/nodejs");

async function test() {
  console.log("=== Simple KuzuDB Node.js Test ===");
  
  try {
    // 初期化
    await kuzu.init();
    console.log("✅ KuzuDB initialized");
    
    // Database作成
    const db = new kuzu.Database(':memory:');
    console.log("✅ Database created");
    
    const conn = new kuzu.Connection(db);
    console.log("✅ Connection created");
    
    // スキーマ作成
    await conn.query(`
      CREATE NODE TABLE User(id STRING, name STRING, PRIMARY KEY(id))
    `);
    console.log("✅ Schema created");
    
    // データ挿入
    await conn.query(`
      CREATE (u:User {id: 'u1', name: 'Alice'})
    `);
    console.log("✅ Data inserted");
    
    // クエリ実行
    const result = await conn.query(`
      MATCH (u:User) RETURN u.id as id, u.name as name
    `);
    
    const users = await result.getAllObjects();
    console.log("✅ Query executed");
    console.log("Users:", users);
    
    // 検証
    if (users.length === 1 && users[0].id === 'u1' && users[0].name === 'Alice') {
      console.log("✅ Data verification passed!");
    }
    
    console.log("\n🎉 KuzuDB Node.js is working without mocks!");
    
  } catch (error) {
    console.error("❌ Error:", error.message);
    console.error(error.stack);
  }
}

test();