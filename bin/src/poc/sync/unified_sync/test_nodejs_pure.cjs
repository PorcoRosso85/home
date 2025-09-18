/**
 * Pure Node.js Test - モックフリー
 * CommonJSのみ使用（ESMインポートなし）
 */

const assert = require('assert');
const kuzu = require("kuzu-wasm/nodejs");

async function runTests() {
  console.log("=== Pure Node.js Test (No Mocks, No ESM) ===\n");

  try {
    // KuzuDB初期化
    await kuzu.init();
    const db = new kuzu.Database(':memory:');
    const conn = new kuzu.Connection(db);
    
    // スキーマ作成
    await conn.query(`
      CREATE NODE TABLE User(id STRING, name STRING, email STRING, PRIMARY KEY(id))
    `);
    await conn.query(`
      CREATE NODE TABLE Post(id STRING, content STRING, authorId STRING, PRIMARY KEY(id))
    `);
    await conn.query(`
      CREATE REL TABLE FOLLOWS(FROM User TO User)
    `);
    
    // 1. CREATE_USER
    console.log("1. Testing CREATE_USER...");
    await conn.query(`
      CREATE (u:User {id: $id, name: $name, email: $email})
    `, { id: 'u1', name: 'Alice', email: 'alice@example.com' });
    
    // 2. UPDATE_USER
    console.log("2. Testing UPDATE_USER...");
    await conn.query(`
      MATCH (u:User {id: $id})
      SET u.name = $name
    `, { id: 'u1', name: 'Alice Updated' });
    
    // 3. CREATE_POST
    console.log("3. Testing CREATE_POST...");
    await conn.query(`
      CREATE (p:Post {id: $id, content: $content, authorId: $authorId})
    `, { id: 'p1', content: 'Hello KuzuDB', authorId: 'u1' });
    
    // 4. FOLLOW_USER
    console.log("4. Testing FOLLOW_USER...");
    await conn.query(`
      CREATE (u:User {id: $id, name: $name, email: $email})
    `, { id: 'u2', name: 'Bob', email: 'bob@example.com' });
    
    await conn.query(`
      MATCH (follower:User {id: $followerId})
      MATCH (target:User {id: $targetId})
      CREATE (follower)-[:FOLLOWS]->(target)
    `, { followerId: 'u1', targetId: 'u2' });
    
    // 検証
    console.log("\n5. Verifying results...");
    
    const userResult = await conn.query(`
      MATCH (u:User) 
      RETURN u.id as id, u.name as name, u.email as email
      ORDER BY u.id
    `);
    const users = await userResult.getAllObjects();
    console.log("Users:", users);
    assert.strictEqual(users.length, 2);
    assert.strictEqual(users[0].name, "Alice Updated");
    assert.strictEqual(users[1].name, "Bob");
    
    const postResult = await conn.query(`
      MATCH (p:Post)
      RETURN p.id as id, p.content as content, p.authorId as authorId
    `);
    const posts = await postResult.getAllObjects();
    console.log("Posts:", posts);
    assert.strictEqual(posts.length, 1);
    assert.strictEqual(posts[0].content, "Hello KuzuDB");
    
    const followResult = await conn.query(`
      MATCH (follower:User)-[:FOLLOWS]->(target:User)
      RETURN follower.id as followerId, target.id as targetId
    `);
    const follows = await followResult.getAllObjects();
    console.log("Follows:", follows);
    assert.strictEqual(follows.length, 1);
    assert.strictEqual(follows[0].followerId, "u1");
    assert.strictEqual(follows[0].targetId, "u2");
    
    console.log("\n🎉 All tests passed without any mocks!");
    console.log("✅ Real KuzuDB Node.js");
    console.log("✅ Real queries");
    console.log("✅ Real data");
    
  } catch (error) {
    console.error("❌ Test failed:", error);
    process.exit(1);
  }
}

runTests();