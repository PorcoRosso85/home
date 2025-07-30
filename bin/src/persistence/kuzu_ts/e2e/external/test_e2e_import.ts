/**
 * External E2E Test for kuzu_ts
 * 
 * This test verifies that kuzu_ts can be used as an external package
 * from another flake/project, simulating real-world usage.
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.224.0/assert/mod.ts";

// Import from the external package using absolute path
// This simulates how other projects would import kuzu_ts
import {
  createDatabase,
  createConnection,
  terminateWorker,
  isDatabase,
  isConnection,
  isValidationError,
  WorkerDatabase,
  WorkerConnection,
  KUZU_VERSION,
  type DatabaseResult,
  type ConnectionResult,
} from "../../mod_worker.ts";

Deno.test("External package - module exports", () => {
  // Verify all expected exports are available
  assertExists(createDatabase, "createDatabase should be exported");
  assertExists(createConnection, "createConnection should be exported");
  assertExists(terminateWorker, "terminateWorker should be exported");
  assertExists(isDatabase, "isDatabase should be exported");
  assertExists(isConnection, "isConnection should be exported");
  assertExists(isValidationError, "isValidationError should be exported");
  assertExists(KUZU_VERSION, "KUZU_VERSION should be exported");
});

Deno.test("External package - version management", () => {
  // Verify KUZU_VERSION is accessible and has the expected format
  console.log(`Using KuzuDB version: ${KUZU_VERSION}`);
  assertExists(KUZU_VERSION, "KUZU_VERSION should be defined");
  assertEquals(typeof KUZU_VERSION, "string", "KUZU_VERSION should be a string");
  
  // Verify version format (semantic versioning)
  const versionPattern = /^\d+\.\d+\.\d+$/;
  assertEquals(
    versionPattern.test(KUZU_VERSION), 
    true, 
    `KUZU_VERSION should match semantic versioning format (got: ${KUZU_VERSION})`
  );
  
  // Example of how external projects would use this version
  // for dependency management or compatibility checks
  const [major, minor, patch] = KUZU_VERSION.split('.').map(Number);
  console.log(`KuzuDB version details - Major: ${major}, Minor: ${minor}, Patch: ${patch}`);
  
  // Example compatibility check
  const minRequiredVersion = "0.6.0";
  const [minMajor, minMinor, minPatch] = minRequiredVersion.split('.').map(Number);
  
  const isCompatible = major > minMajor || 
    (major === minMajor && minor > minMinor) ||
    (major === minMajor && minor === minMinor && patch >= minPatch);
    
  assertEquals(isCompatible, true, `KuzuDB version ${KUZU_VERSION} should be >= ${minRequiredVersion}`);
});

Deno.test({
  name: "External package - basic database operations",
  sanitizeResources: false,
  sanitizeOps: false,
  fn: async () => {
  console.log("Creating in-memory database...");
  const dbResult = await createDatabase(":memory:");
  
  console.log("Database result:", dbResult);
  console.log("Is WorkerDatabase?", dbResult instanceof WorkerDatabase);
  console.log("Is validation error?", isValidationError(dbResult));
  
  // Check if database was created successfully
  if (isValidationError(dbResult)) {
    throw new Error(`Failed to create database: ${dbResult.message}`);
  }
  
  // For Worker implementation, check for WorkerDatabase instance
  assertEquals(dbResult instanceof WorkerDatabase, true, "Should return a valid WorkerDatabase instance");
  
  console.log("Creating connection...");
  const connResult = await createConnection(dbResult);
  
  // Check if connection was created successfully
  if (isValidationError(connResult)) {
    throw new Error(`Failed to create connection: ${connResult.message}`);
  }
  
  // For Worker implementation, check for WorkerConnection instance
  assertEquals(connResult instanceof WorkerConnection, true, "Should return a valid WorkerConnection instance");
  
  // Test basic query operations
  console.log("Creating table...");
  await connResult.query("CREATE NODE TABLE TestNode(id INT64, name STRING, PRIMARY KEY(id))");
  
  console.log("Inserting data...");
  await connResult.query("CREATE (n:TestNode {id: 1, name: 'Test'})");
  
  console.log("Querying data...");
  const result = await connResult.query("MATCH (n:TestNode) RETURN n.id, n.name");
  const rows = await result.getAll();
  
  assertEquals(rows.length, 1, "Should have one row");
  // Worker returns objects, not arrays
  assertEquals(rows[0]["n.id"], 1, "Should return correct id");
  assertEquals(rows[0]["n.name"], "Test", "Should return correct name");
  
  // Clean up
  console.log("Cleaning up...");
  await connResult.close();
  await dbResult.close();
  
  console.log("✅ All operations completed successfully");
  }
});

// Ensure worker is terminated after all tests
Deno.test("Cleanup - terminate worker", () => {
  terminateWorker();
  console.log("Worker terminated successfully");
});