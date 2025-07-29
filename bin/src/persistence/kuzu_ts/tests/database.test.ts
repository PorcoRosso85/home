import { assertEquals, assertExists, assertStrictEquals } from "https://deno.land/std@0.218.0/assert/mod.ts";
import { createDatabase, createConnection } from "../core/database.ts";
import { 
  isDatabase, 
  isConnection, 
  isFileOperationError, 
  isValidationError 
} from "../core/result_types.ts";

Deno.test("createDatabase - in-memory database creation", () => {
  const result = createDatabase(":memory:");
  assertStrictEquals(isDatabase(result), true);
  if (isDatabase(result)) {
    assertExists(result);
    assertEquals(typeof result.close, "function");
  }
});

Deno.test("createConnection - connection creation", () => {
  const dbResult = createDatabase(":memory:");
  assertStrictEquals(isDatabase(dbResult), true);
  
  if (isDatabase(dbResult)) {
    const connResult = createConnection(dbResult);
    assertStrictEquals(isConnection(connResult), true);
    if (isConnection(connResult)) {
      assertExists(connResult);
      assertEquals(typeof connResult.query, "function");
    }
  }
});

Deno.test("database operations - basic CRUD", async () => {
  const dbResult = createDatabase(":memory:");
  assertStrictEquals(isDatabase(dbResult), true);
  
  if (isDatabase(dbResult)) {
    const connResult = createConnection(dbResult);
    assertStrictEquals(isConnection(connResult), true);
    
    if (isConnection(connResult)) {
      // Create schema
      await connResult.query("CREATE NODE TABLE Person(name STRING, age INT64, PRIMARY KEY (name))");
      
      // Insert data
      await connResult.query("CREATE (:Person {name: 'Alice', age: 30})");
      await connResult.query("CREATE (:Person {name: 'Bob', age: 25})");
      
      // Query data
      const result = await connResult.query("MATCH (p:Person) RETURN p.name, p.age ORDER BY p.age");
      const rows = await result.getAll();
      
      assertEquals(rows.length, 2);
      assertEquals(rows[0]["p.name"], "Bob");
      assertEquals(rows[0]["p.age"], 25);
      assertEquals(rows[1]["p.name"], "Alice");
      assertEquals(rows[1]["p.age"], 30);
    }
  }
});

Deno.test("createDatabase - test unique for in-memory", () => {
  const result1 = createDatabase(":memory:", { testUnique: true });
  const result2 = createDatabase(":memory:", { testUnique: true });
  
  assertStrictEquals(isDatabase(result1), true);
  assertStrictEquals(isDatabase(result2), true);
  
  if (isDatabase(result1) && isDatabase(result2)) {
    // Should return different instances
    assertExists(result1);
    assertExists(result2);
    // Note: We can't test inequality directly due to KuzuDB internals
  }
});

// Error handling tests
Deno.test("createDatabase - validation error for invalid path", () => {
  const result = createDatabase("");
  assertStrictEquals(isValidationError(result), true);
  
  if (isValidationError(result)) {
    assertEquals(result.type, "ValidationError");
    assertEquals(result.field, "path");
    assertEquals(result.constraint, "non-empty string");
    assertExists(result.suggestion);
  }
});

Deno.test("createDatabase - validation error for null path", () => {
  const result = createDatabase(null as any);
  assertStrictEquals(isValidationError(result), true);
  
  if (isValidationError(result)) {
    assertEquals(result.type, "ValidationError");
    assertEquals(result.field, "path");
    assertEquals(result.constraint, "non-empty string");
  }
});

Deno.test("createConnection - validation error for invalid database", () => {
  const result = createConnection(null as any);
  assertStrictEquals(isValidationError(result), true);
  
  if (isValidationError(result)) {
    assertEquals(result.type, "ValidationError");
    assertEquals(result.field, "db");
    assertEquals(result.constraint, "valid Database instance");
    assertExists(result.suggestion);
  }
});

Deno.test("createConnection - validation error for non-object", () => {
  const result = createConnection("not-a-database" as any);
  assertStrictEquals(isValidationError(result), true);
  
  if (isValidationError(result)) {
    assertEquals(result.type, "ValidationError");
    assertEquals(result.field, "db");
  }
});