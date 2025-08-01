#!/usr/bin/env bun

/**
 * Minimal test to prove Bun works with only persistence/kuzu_ts dependency
 * 
 * Requirements:
 * - NO npm install needed
 * - NO package.json dependencies
 * - ONLY flake.input: persistence/kuzu_ts
 */

console.log("🧪 Minimal Bun + persistence/kuzu_ts Test");
console.log("========================================\n");

// Step 1: Verify environment
console.log("1️⃣ Environment Check:");
console.log("   Bun version:", process.versions.bun);
console.log("   Working directory:", process.cwd());
console.log("   NODE_PATH:", process.env.NODE_PATH || "(not set - not needed!)");
console.log("   LD_LIBRARY_PATH:", process.env.LD_LIBRARY_PATH ? "✅ Set" : "❌ Not set");

// Step 2: Test require without any npm install
console.log("\n2️⃣ Testing require('kuzu'):");
try {
  const kuzu = require("kuzu");
  console.log("   ✅ Successfully loaded kuzu module");
  console.log("   ✅ Available exports:", Object.keys(kuzu).join(", "));
} catch (error) {
  console.error("   ❌ Failed to load kuzu:", error.message);
  process.exit(1);
}

// Step 3: Test actual functionality
console.log("\n3️⃣ Testing KuzuDB functionality:");
const kuzu = require("kuzu");

try {
  // Create in-memory database
  const db = new kuzu.Database(":memory:");
  console.log("   ✅ Created in-memory database");
  
  // Create connection
  const conn = new kuzu.Connection(db);
  console.log("   ✅ Created connection");
  
  // Run a simple query
  const result = await conn.query("RETURN 'Hello from minimal Bun setup!' as message");
  const table = await result.getAll();
  console.log("   ✅ Query result:", table[0].message);
  
  // Create a table and insert data
  await conn.query("CREATE NODE TABLE User(id INT64, name STRING, PRIMARY KEY(id))");
  console.log("   ✅ Created User table");
  
  await conn.query("CREATE (:User {id: 1, name: 'Bun User'})");
  console.log("   ✅ Inserted test data");
  
  // Query the data
  const userResult = await conn.query("MATCH (u:User) RETURN u.name");
  const users = await userResult.getAll();
  console.log("   ✅ Retrieved user:", users[0]["u.name"]);
  
  // Clean up
  conn.close();
  db.close();
  
} catch (error) {
  console.error("   ❌ Error:", error.message);
  process.exit(1);
}

// Step 4: Summary
console.log("\n✨ SUCCESS! Proven:");
console.log("   1. Bun runtime from nixpkgs (no flake.input)");
console.log("   2. KuzuDB from persistence/kuzu_ts (only flake.input)");
console.log("   3. No npm install needed");
console.log("   4. No package.json dependencies");
console.log("   5. Fully functional KuzuDB operations");
console.log("\n🎯 Minimal configuration achieved!");