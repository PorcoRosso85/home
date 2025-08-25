#!/usr/bin/env node
/**
 * Node.js environment test for kuzu-wasm
 * Run with: node test-nodejs.js
 */

const kuzu = require('kuzu-wasm/nodejs');

async function testNodeJS() {
  console.log('🟢 Testing kuzu-wasm in Node.js environment...');
  
  try {
    // Create in-memory database
    const db = new kuzu.Database(':memory:');
    console.log('✅ Database created');
    
    // Create connection
    const conn = new kuzu.Connection(db);
    console.log('✅ Connection established');
    
    // Create schema
    await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY(name))");
    console.log('✅ Schema created');
    
    // Insert data
    await conn.query("CREATE (:Person {name: 'Alice', age: 30})");
    await conn.query("CREATE (:Person {name: 'Bob', age: 25})");
    console.log('✅ Data inserted');
    
    // Query data
    const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
    const data = await result.getAllObjects();
    console.log('✅ Query results:', data);
    
    // Cleanup
    await result.close();
    await conn.close();
    await db.close();
    await kuzu.close();
    console.log('✅ Cleanup complete');
    
    console.log('\n🎉 Node.js test passed successfully!');
  } catch (error) {
    console.error('❌ Error:', error);
    process.exit(1);
  }
}

testNodeJS();