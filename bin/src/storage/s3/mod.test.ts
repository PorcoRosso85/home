/**
 * Minimal tests for mod.ts exports
 * Ensures the library can be used when imported as a flake input
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";

Deno.test("mod.ts exports createStorageAdapter", async () => {
  const mod = await import("./mod.ts");
  assertExists(mod.createStorageAdapter);
  
  // Verify it creates an adapter
  const adapter = mod.createStorageAdapter({ type: "in-memory" });
  assertEquals(adapter.getType(), "in-memory");
});

Deno.test("mod.ts exports S3StorageApplication", async () => {
  const mod = await import("./mod.ts");
  assertExists(mod.S3StorageApplication);
  
  // Verify it can be instantiated
  const app = new mod.S3StorageApplication({ type: "in-memory" });
  assertExists(app.execute);
});

Deno.test("mod.ts exports required types", async () => {
  const mod = await import("./mod.ts");
  
  // These are type exports, so we just verify the module loads
  assertExists(mod);
  
  // Test that we can use the types in type annotations
  type TestTypes = {
    adapter: mod.StorageAdapter;
    config: mod.StorageConfig;
    command: mod.S3Command;
    result: mod.S3Result;
  };
  
  // If this compiles, types are exported correctly
  const _: TestTypes = {} as any;
});

Deno.test("Library works with minimal setup", async () => {
  const { createStorageAdapter, S3StorageApplication } = await import("./mod.ts");
  
  // Test adapter creation and basic operation
  const adapter = createStorageAdapter({ type: "in-memory" });
  await adapter.upload("test.txt", "Hello from flake!");
  
  const result = await adapter.download("test.txt");
  const content = new TextDecoder().decode(result.content);
  assertEquals(content, "Hello from flake!");
});

Deno.test("S3StorageApplication executes commands", async () => {
  const { S3StorageApplication } = await import("./mod.ts");
  
  const app = new S3StorageApplication({ type: "in-memory" });
  
  // Upload
  const uploadResult = await app.execute({
    type: "upload",
    key: "app-test.txt",
    content: "Application test"
  });
  assertEquals(uploadResult.type, "upload");
  
  // List
  const listResult = await app.execute({ type: "list" });
  assertEquals(listResult.type, "list");
  if (listResult.type === "list") {
    assertEquals(listResult.objects.length, 1);
  }
});

Deno.test("InMemoryStorageAdapter is directly accessible", async () => {
  const { InMemoryStorageAdapter } = await import("./mod.ts");
  assertExists(InMemoryStorageAdapter);
  
  const adapter = new InMemoryStorageAdapter();
  assertEquals(adapter.getType(), "in-memory");
});