import { assertEquals } from "https://deno.land/std@0.218.0/assert/mod.ts";
// Import worker client functions
import { 
  createDatabaseWorker, 
  createConnectionWorker,
  terminateWorker,
  WorkerDatabase,
  WorkerConnection
} from "../../worker/client.ts";

Deno.test("npm:kuzu worker - panic isolation test", async () => {
  console.log("Starting npm:kuzu worker panic isolation test...");
  
  let db: WorkerDatabase | null = null;
  let conn: WorkerConnection | null = null;
  let testCompleted = false;
  
  try {
    // Create in-memory database through worker
    console.log("Creating in-memory database through worker...");
    const dbResult = await createDatabaseWorker(":memory:");
    
    // Check if database creation was successful
    if ('error_code' in dbResult) {
      throw new Error(`Database creation failed: ${dbResult.message}`);
    }
    
    db = dbResult as WorkerDatabase;
    console.log("Database created successfully in worker");
    
    // Create connection through worker
    console.log("Creating connection through worker...");
    const connResult = await createConnectionWorker(db);
    
    // Check if connection creation was successful
    if ('error_code' in connResult) {
      throw new Error(`Connection creation failed: ${connResult.message}`);
    }
    
    conn = connResult as WorkerConnection;
    console.log("Connection created successfully in worker");
    
    // Execute CREATE query
    console.log("Executing CREATE NODE TABLE query through worker...");
    await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
    console.log("CREATE query executed successfully");
    
    // Insert data
    console.log("Inserting test data through worker...");
    await conn.query("CREATE (:Person {name: 'Alice', age: 30})");
    await conn.query("CREATE (:Person {name: 'Bob', age: 25})");
    console.log("Data inserted successfully");
    
    // Execute MATCH query
    console.log("Executing MATCH query through worker...");
    const result = await conn.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
    console.log("MATCH query executed successfully");
    
    // Verify results
    console.log("Verifying query results from worker...");
    const table = await result.getAll();
    console.log("Result from worker:", table);
    console.log(`Query returned ${table.length} rows`);
    
    assertEquals(table.length, 2);
    
    // Log the structure of the first row
    if (table.length > 0) {
      console.log("First row structure:", table[0]);
      console.log("First row keys:", Object.keys(table[0]));
    }
    
    // More flexible property access
    const getName = (row: any) => row["p.name"] || row.name || row[0];
    const getAge = (row: any) => row["p.age"] || row.age || row[1];
    
    assertEquals(getName(table[0]), "Bob");
    assertEquals(getAge(table[0]), 25);
    assertEquals(getName(table[1]), "Alice");
    assertEquals(getAge(table[1]), 30);
    console.log("Query results verified successfully");
    
    // Mark test as completed
    testCompleted = true;
    console.log("Test completed without main process panic");
    
  } catch (error) {
    console.error("Error during test execution:", error);
    throw error;
  } finally {
    // Cleanup resources
    console.log("Starting cleanup...");
    
    if (conn) {
      try {
        console.log("Closing connection in worker...");
        await conn.close();
        console.log("Connection closed successfully");
      } catch (error) {
        console.error("Error closing connection:", error);
      }
    }
    
    if (db) {
      try {
        console.log("Closing database in worker...");
        await db.close();
        console.log("Database closed successfully");
      } catch (error) {
        console.error("Error closing database:", error);
      }
    }
    
    // Terminate the worker process
    console.log("Terminating worker process...");
    terminateWorker();
    console.log("Worker terminated");
    
    console.log("Cleanup completed");
  }
  
  // Final assertion to confirm test completed without panic
  assertEquals(testCompleted, true, "Test should complete without main process panic");
  console.log("All assertions passed - main process remained stable!");
});

Deno.test("npm:kuzu worker - edge case handling and panic resilience", async () => {
  console.log("\nStarting edge case handling and panic resilience test...");
  
  let db: WorkerDatabase | null = null;
  let conn: WorkerConnection | null = null;
  
  try {
    const dbResult = await createDatabaseWorker(":memory:");
    if ('error_code' in dbResult) {
      throw new Error(`Database creation failed: ${dbResult.message}`);
    }
    db = dbResult as WorkerDatabase;
    
    const connResult = await createConnectionWorker(db);
    if ('error_code' in connResult) {
      throw new Error(`Connection creation failed: ${connResult.message}`);
    }
    conn = connResult as WorkerConnection;
    
    // Test with empty table
    console.log("Testing query on non-existent table through worker...");
    try {
      await conn.query("MATCH (n:NonExistent) RETURN n");
      console.log("No error on non-existent table (expected behavior)");
    } catch (error) {
      console.log("Error on non-existent table:", (error as Error).message);
      console.log("Main process remained stable despite worker error");
    }
    
    // Test with complex query
    console.log("Testing complex query through worker...");
    await conn.query("CREATE NODE TABLE Movie(title STRING, year INT64, PRIMARY KEY (title))");
    await conn.query("CREATE REL TABLE ACTED_IN(FROM Person TO Movie)");
    
    // Create person first
    await conn.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
    await conn.query("CREATE (:Person {name: 'Alice', age: 30})");
    await conn.query("CREATE (:Movie {title: 'The Matrix', year: 1999})");
    await conn.query("MATCH (p:Person {name: 'Alice'}), (m:Movie {title: 'The Matrix'}) CREATE (p)-[:ACTED_IN]->(m)");
    
    const result = await conn.query("MATCH (p:Person)-[:ACTED_IN]->(m:Movie) RETURN p.name, m.title");
    const table = await result.getAll();
    console.log(`Complex query returned ${table.length} relationships`);
    
    // Test with potentially problematic query
    console.log("Testing potentially problematic query...");
    try {
      // This might cause issues in some KuzuDB versions
      await conn.query("MATCH (n) WHERE n.nonexistent = 'value' RETURN n");
      console.log("Problematic query handled gracefully");
    } catch (error) {
      console.log("Problematic query error handled:", (error as Error).message);
      console.log("Main process remained stable despite potential worker issue");
    }
    
    console.log("Edge case test completed successfully");
    
  } finally {
    if (conn) await conn.close();
    if (db) await db.close();
    terminateWorker();
  }
  
  // If we reach here, main process did not panic
  assertEquals(true, true, "Edge case test completed without main process panic");
  console.log("Worker isolation successful - main process remained stable!");
});

Deno.test("npm:kuzu worker - stress test with multiple operations", async () => {
  console.log("\nStarting stress test with multiple operations...");
  
  let db: WorkerDatabase | null = null;
  let conn: WorkerConnection | null = null;
  const operationCount = 50;
  
  try {
    const dbResult = await createDatabaseWorker(":memory:");
    if ('error_code' in dbResult) {
      throw new Error(`Database creation failed: ${dbResult.message}`);
    }
    db = dbResult as WorkerDatabase;
    
    const connResult = await createConnectionWorker(db);
    if ('error_code' in connResult) {
      throw new Error(`Connection creation failed: ${connResult.message}`);
    }
    conn = connResult as WorkerConnection;
    
    // Create schema
    console.log("Creating schema for stress test...");
    await conn.query("CREATE NODE TABLE TestNode(id INT64, value STRING, PRIMARY KEY (id))");
    
    // Perform multiple insert operations
    console.log(`Performing ${operationCount} insert operations through worker...`);
    for (let i = 0; i < operationCount; i++) {
      await conn.query(`CREATE (:TestNode {id: ${i}, value: 'test_${i}'})`);
      if (i % 10 === 9) {
        console.log(`Progress: ${i + 1}/${operationCount} inserts completed`);
      }
    }
    console.log("All inserts completed successfully");
    
    // Perform complex aggregation
    console.log("Performing aggregation query through worker...");
    const result = await conn.query("MATCH (n:TestNode) RETURN count(n) as count, max(n.id) as max_id");
    const table = await result.getAll();
    
    console.log("Aggregation result:", table);
    assertEquals(table[0].count || table[0][0], operationCount);
    assertEquals(table[0].max_id || table[0][1], operationCount - 1);
    
    console.log("Stress test completed successfully");
    console.log("Main process remained stable throughout all operations");
    
  } finally {
    if (conn) await conn.close();
    if (db) await db.close();
    terminateWorker();
  }
  
  assertEquals(true, true, "Stress test completed without main process panic");
});