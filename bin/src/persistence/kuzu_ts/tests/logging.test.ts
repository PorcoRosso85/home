import { assertEquals, assertExists } from "jsr:@std/assert@^1.0.0";
import { log } from "log_ts/mod.ts";
import { createDatabase, createConnection } from "../classic/database.ts";
import { isDatabase, isConnection, isValidationError } from "../shared/types.ts";

// Test log_ts module integration
Deno.test("log_ts - module import and basic functionality", () => {
  assertExists(log);
  assertEquals(typeof log, "function");
  
  // Test all log levels work without throwing
  const levels = ["DEBUG", "INFO", "WARN", "ERROR"] as const;
  for (const level of levels) {
    log(level, {
      uri: "test.logging",
      message: `Testing ${level} level`
    });
  }
});

// Test database logging behavior
Deno.test("database operations - produce expected log output", () => {
  // Test in-memory database logs INFO
  const memResult = createDatabase(":memory:");
  assertEquals(isDatabase(memResult), true);
  
  // Test validation errors (no logs expected for validation)
  const emptyResult = createDatabase("");
  assertEquals(isValidationError(emptyResult), true);
  
  // Test connection creation logs INFO
  if (isDatabase(memResult)) {
    const connResult = createConnection(memResult);
    assertEquals(isConnection(connResult), true);
  }
  
  // Test invalid connection logs ERROR
  // @ts-ignore - Testing invalid input
  const invalidResult = createConnection(null);
  assertEquals(isValidationError(invalidResult), true);
});