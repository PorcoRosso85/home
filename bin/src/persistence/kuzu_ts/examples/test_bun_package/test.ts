// Test importing and using KuzuDB from the packaged Bun version
// This test directly imports kuzu from node_modules to verify the package works

console.log("Starting KuzuDB Bun package test...\n");

// First, let's check if we can access the packaged files
const kuzuPath = process.env.KUZU_TS_PATH;
console.log("KUZU_TS_PATH:", kuzuPath);

async function runTest() {
  try {
    // Import kuzu directly from the linked node_modules
    const kuzu = require("kuzu");
    console.log("✓ Successfully imported kuzu module using require()");
    
    // Create a simple database to test functionality
    const db = new kuzu.Database(":memory:");
    console.log("✓ Successfully created KuzuDB instance");
    
    // Create a connection - using the correct API
    const conn = new kuzu.Connection(db);
    console.log("✓ Successfully created database connection");
    
    // Create a simple schema
    await conn.query("CREATE NODE TABLE Person(id INT64, name STRING, PRIMARY KEY(id))");
    console.log("✓ Successfully created Person table");
    
    // Insert some data
    await conn.query("CREATE (:Person {id: 1, name: 'Alice'})");
    await conn.query("CREATE (:Person {id: 2, name: 'Bob'})");
    console.log("✓ Successfully inserted test data");
    
    // Query the data
    const result = await conn.query("MATCH (p:Person) RETURN p.name ORDER BY p.id");
    const table = await result.getAll();
    const names = table.map(row => row["p.name"]);
    console.log("✓ Successfully queried data:", names);
    
    // Verify the results
    if (names.length === 2 && names[0] === "Alice" && names[1] === "Bob") {
      console.log("\n✅ All tests passed! External project can successfully use the Bun package.");
      console.log("   The kuzu npm module is properly packaged and functional with Bun runtime.");
      console.log("   The native bindings are correctly linked and operational.");
    } else {
      throw new Error("Query results don't match expected values");
    }
    
    // Clean up
    conn.close();
    db.close();
    
  } catch (error) {
    console.error("\n❌ Test failed:", error);
    console.error("   Error details:", error.message);
    console.error("   Stack trace:", error.stack);
    console.error("   The Bun package may not be properly configured for external use.");
    process.exit(1);
  }
}

// Run the async test
runTest().catch(console.error);