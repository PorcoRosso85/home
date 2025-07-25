/**
 * Tests for In-Memory Storage Provider
 * Uses the common testStorageAdapter function to ensure consistency
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createStorageAdapter } from "../adapter.ts";
import { testStorageAdapter, verifyObjectSorting, verifyOverwriteBehavior, createTestContent } from "./test-helpers.ts";

// Run comprehensive test suite for in-memory adapter
Deno.test("in-memory adapter: comprehensive test suite", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  await testStorageAdapter(adapter, "in-memory");
});

// Additional in-memory specific tests
Deno.test("in-memory adapter: handles large content efficiently", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Create 10MB test content
  const largeContent = createTestContent(10 * 1024 * 1024);
  const key = "large-file.bin";
  
  // Upload and verify
  await adapter.upload(key, largeContent);
  const downloaded = await adapter.download(key);
  
  assertEquals(downloaded.content.length, largeContent.length);
  assertEquals(downloaded.content[0], largeContent[0]);
  assertEquals(downloaded.content[largeContent.length - 1], largeContent[largeContent.length - 1]);
  
  // Cleanup
  await adapter.delete([key]);
});

// Test using individual helper functions
Deno.test("in-memory adapter: sorting behavior", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  await verifyObjectSorting(adapter);
});

Deno.test("in-memory adapter: overwrite behavior", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  await verifyOverwriteBehavior(adapter);
});