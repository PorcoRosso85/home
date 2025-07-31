#!/usr/bin/env bun

import { createDatabase, createConnection, executeQuery, getAllRows } from "./mod.ts";

async function testKuzuDBWithBun() {
  console.log("Testing KuzuDB with Bun using simple wrapper...\n");

  try {
    // Create an in-memory database
    console.log("1. Creating in-memory database...");
    const database = await createDatabase(":memory:");
    console.log("✓ Database created successfully");

    // Create a connection
    console.log("\n2. Creating connection...");
    const connection = await createConnection(database);
    console.log("✓ Connection created successfully");

    // Create a simple table
    console.log("\n3. Creating test table...");
    await executeQuery(connection, `
      CREATE NODE TABLE Person(
        name STRING,
        age INT64,
        PRIMARY KEY (name)
      )
    `);
    console.log("✓ Table created successfully");

    // Insert test data
    console.log("\n4. Inserting test data...");
    await executeQuery(connection, `
      CREATE (:Person {name: 'Alice', age: 30}),
             (:Person {name: 'Bob', age: 25})
    `);
    console.log("✓ Data inserted successfully");

    // Query the data
    console.log("\n5. Querying data...");
    const result = await executeQuery(connection, "MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
    const rows = getAllRows(result);
    
    console.log("✓ Query executed successfully");
    console.log("\nResults:");
    console.table(rows);

    // Clean up
    connection.close();
    database.close();

    console.log("\n✅ All tests passed! Bun can successfully use KuzuDB with simple wrapper.");
    return true;
  } catch (error) {
    console.error("\n❌ Test failed with error:");
    console.error(error);
    return false;
  }
}

// Run the test
testKuzuDBWithBun().then((success) => {
  process.exit(success ? 0 : 1);
});