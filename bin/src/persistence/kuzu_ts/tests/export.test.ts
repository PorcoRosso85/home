import { assertEquals, assertExists } from "https://deno.land/std@0.218.0/assert/mod.ts";

Deno.test("kuzu exports - verify all required exports exist", async () => {
  // Test direct npm import
  const kuzu = await import("npm:kuzu@0.10.0");
  
  // Verify exports exist
  assertExists(kuzu.Database, "Database should be exported");
  assertExists(kuzu.Connection, "Connection should be exported");
  assertExists(kuzu.PreparedStatement, "PreparedStatement should be exported");
  assertExists(kuzu.QueryResult, "QueryResult should be exported");
  assertExists(kuzu.VERSION, "VERSION should be exported");
  assertExists(kuzu.STORAGE_VERSION, "STORAGE_VERSION should be exported");
  
  // Verify types
  assertEquals(typeof kuzu.Database, "function", "Database should be a constructor");
  assertEquals(typeof kuzu.Connection, "function", "Connection should be a constructor");
  assertEquals(typeof kuzu.PreparedStatement, "function", "PreparedStatement should be a constructor");
  assertEquals(typeof kuzu.QueryResult, "function", "QueryResult should be a constructor");
  assertEquals(typeof kuzu.VERSION, "string", "VERSION should be a string");
  assertEquals(typeof kuzu.STORAGE_VERSION, "number", "STORAGE_VERSION should be a number");
});

Deno.test("named imports - verify named imports work correctly", async () => {
  // This is how we import in our code
  const { Database, Connection } = await import("kuzu");
  
  assertExists(Database, "Database should be available via named import");
  assertExists(Connection, "Connection should be available via named import");
  
  assertEquals(typeof Database, "function", "Database should be a constructor");
  assertEquals(typeof Connection, "function", "Connection should be a constructor");
});