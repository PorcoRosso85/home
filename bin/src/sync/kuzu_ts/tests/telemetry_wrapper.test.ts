import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createTelemetryWrapper } from "../telemetry_wrapper.ts";

Deno.test("createTelemetryWrapper creates a logger with dynamic URI", () => {
  // Arrange
  const baseUri = "kuzu:sync:test";
  const wrapper = createTelemetryWrapper(baseUri);
  
  // Assert wrapper exists
  assertExists(wrapper);
  assertExists(wrapper.log);
  assertExists(wrapper.setUri);
  
  // Test that log function exists and has correct signature
  assertEquals(typeof wrapper.log, "function");
  assertEquals(typeof wrapper.setUri, "function");
});

Deno.test("telemetry wrapper logs with base URI", () => {
  // Arrange
  const baseUri = "kuzu:sync:test";
  const wrapper = createTelemetryWrapper(baseUri);
  let capturedLog: { level: string; data: Record<string, unknown> } | undefined;
  
  // Mock the log function to capture output
  const originalLog = globalThis.console.log;
  globalThis.console.log = (output: string) => {
    try {
      capturedLog = { level: "info", data: JSON.parse(output) };
    } catch {
      // Not JSON, ignore
    }
  };
  
  try {
    // Act
    wrapper.log("info", { message: "Test message" });
    
    // Assert
    assertExists(capturedLog);
    assertEquals(capturedLog!.data.uri, baseUri);
    assertEquals(capturedLog!.data.message, "Test message");
  } finally {
    // Restore original console.log
    globalThis.console.log = originalLog;
  }
});

Deno.test("telemetry wrapper allows dynamic URI update", () => {
  // Arrange
  const baseUri = "kuzu:sync:test";
  const newUri = "kuzu:sync:updated";
  const wrapper = createTelemetryWrapper(baseUri);
  let capturedLog: { level: string; data: Record<string, unknown> } | undefined;
  
  // Mock the log function to capture output
  const originalLog = globalThis.console.log;
  globalThis.console.log = (output: string) => {
    try {
      capturedLog = { level: "info", data: JSON.parse(output) };
    } catch {
      // Not JSON, ignore
    }
  };
  
  try {
    // Act - update URI
    wrapper.setUri(newUri);
    wrapper.log("info", { message: "Test with new URI" });
    
    // Assert
    assertExists(capturedLog);
    assertEquals(capturedLog!.data.uri, newUri);
    assertEquals(capturedLog!.data.message, "Test with new URI");
  } finally {
    // Restore original console.log
    globalThis.console.log = originalLog;
  }
});

Deno.test("telemetry wrapper preserves additional data fields", () => {
  // Arrange
  const baseUri = "kuzu:sync:test";
  const wrapper = createTelemetryWrapper(baseUri);
  let capturedLog: { level: string; data: Record<string, unknown> } | undefined;
  
  // Mock the log function to capture output
  const originalLog = globalThis.console.log;
  globalThis.console.log = (output: string) => {
    try {
      capturedLog = { level: "debug", data: JSON.parse(output) };
    } catch {
      // Not JSON, ignore
    }
  };
  
  try {
    // Act
    wrapper.log("debug", { 
      message: "Test with extra data",
      userId: "user123",
      action: "sync",
      timestamp: "2025-01-28T10:00:00Z"
    });
    
    // Assert
    assertExists(capturedLog);
    assertEquals(capturedLog!.data.uri, baseUri);
    assertEquals(capturedLog!.data.message, "Test with extra data");
    assertEquals(capturedLog!.data.userId, "user123");
    assertEquals(capturedLog!.data.action, "sync");
    assertEquals(capturedLog!.data.timestamp, "2025-01-28T10:00:00Z");
  } finally {
    // Restore original console.log
    globalThis.console.log = originalLog;
  }
});

Deno.test("telemetry wrapper supports method chaining for URI updates", () => {
  // Arrange
  const baseUri = "kuzu:sync:test";
  const wrapper = createTelemetryWrapper(baseUri);
  
  // Act - test method chaining
  const result = wrapper.setUri("kuzu:sync:chained");
  
  // Assert
  assertEquals(result, wrapper); // Should return itself for chaining
});