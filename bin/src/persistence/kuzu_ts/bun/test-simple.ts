#!/usr/bin/env bun

// Direct import of the kuzu npm package to test basic functionality
const kuzu = require("kuzu");

async function testKuzuDBDirectly() {
  console.log("Testing KuzuDB directly with Bun (npm:kuzu)...\n");

  try {
    // Create an in-memory database
    console.log("1. Creating in-memory database...");
    const database = new kuzu.Database(":memory:");
    console.log("✓ Database created successfully");

    // Create a connection
    console.log("\n2. Creating connection...");
    const connection = new kuzu.Connection(database);
    console.log("✓ Connection created successfully");

    // Execute a simple query
    console.log("\n3. Testing basic query...");
    const result = await connection.query("RETURN 'Hello from KuzuDB!' as message");
    const data = await result.getAll();
    
    console.log("✓ Query executed successfully");
    console.log("Result:", data[0]);

    console.log("\n✅ Success! Bun can use the npm:kuzu module directly.");
    return true;
  } catch (error) {
    console.error("\n❌ Test failed with error:");
    console.error(error);
    return false;
  }
}

// Run the test
testKuzuDBDirectly().then((success) => {
  process.exit(success ? 0 : 1);
});