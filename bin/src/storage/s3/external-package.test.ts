/**
 * External Package Usage Tests
 * Tests the package from an external consumer perspective
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";

// Test 1: Module exports are properly accessible
Deno.test("Package exports all required modules", async () => {
  // Main module
  const mod = await import("./mod.ts");
  assertExists(mod.createStorageAdapter);
  assertExists(mod.S3StorageApplication);
  
  // Domain exports
  const domain = await import("./domain.ts");
  assertExists(domain.S3Command);
  assertExists(domain.S3Result);
  assertExists(domain.StorageObject);
  
  // Adapter exports
  const adapter = await import("./adapter.ts");
  assertExists(adapter.StorageAdapter);
  assertExists(adapter.createStorageAdapter);
  
  // Provider exports
  const providers = await import("./providers/mod.ts");
  assertExists(providers.createStorageAdapter);
  assertExists(providers.InMemoryStorageAdapter);
});

Deno.test("Package can be used as external dependency", async () => {
  // Simulate external package usage
  const { createStorageAdapter } = await import("./mod.ts");
  
  // Should create adapter without environment setup
  const adapter = createStorageAdapter({ type: "in-memory" });
  assertEquals(adapter.getType(), "in-memory");
  
  // Should perform basic operations
  const uploadResult = await adapter.upload("test.txt", "Hello Package!");
  assertEquals(uploadResult.key, "test.txt");
  
  const downloadResult = await adapter.download("test.txt");
  const content = new TextDecoder().decode(downloadResult.content);
  assertEquals(content, "Hello Package!");
});

Deno.test("Package types are properly exported", () => {
  // This test verifies TypeScript compilation
  // In a real scenario, this would be tested by building a TypeScript project
  // that imports our package
  
  type TestImports = {
    StorageAdapter: import("./adapter.ts").StorageAdapter;
    S3Command: import("./domain.ts").S3Command;
    StorageObject: import("./domain.ts").StorageObject;
    StorageConfig: import("./adapter.ts").StorageConfig;
  };
  
  // Type-level test passes if this compiles
  const _typeTest: TestImports = {} as any;
});

Deno.test("Package works with minimal configuration", async () => {
  const { S3StorageApplication } = await import("./mod.ts");
  
  // Create application with minimal config
  const app = new S3StorageApplication({ type: "in-memory" });
  
  // Execute basic workflow
  const uploadCmd = { 
    type: "upload" as const, 
    key: "minimal.txt", 
    content: "Minimal config test" 
  };
  const uploadResult = await app.execute(uploadCmd);
  assertEquals(uploadResult.type, "upload");
  assertEquals("key" in uploadResult && uploadResult.key, "minimal.txt");
  
  const listCmd = { type: "list" as const };
  const listResult = await app.execute(listCmd);
  assertEquals(listResult.type, "list");
  assertEquals("objects" in listResult && listResult.objects.length, 1);
});

Deno.test("Package handles missing dependencies gracefully", async () => {
  // Test behavior when AWS SDK is not available
  const { createStorageAdapter } = await import("./mod.ts");
  
  // Should fall back to in-memory when S3 dependencies are missing
  const adapter = createStorageAdapter({ type: "auto" });
  assertEquals(adapter.getType(), "in-memory");
});

Deno.test("Package version and metadata are accessible", async () => {
  // In a real package, this would read from package.json or deno.json
  const denoConfig = await Deno.readTextFile("./deno.json");
  const config = JSON.parse(denoConfig);
  
  assertExists(config.exports);
  assertExists(config.tasks);
  assertExists(config.imports);
});

Deno.test("Package readme examples work correctly", async () => {
  // Test that README code examples actually work
  const { createStorageAdapter } = await import("./mod.ts");
  
  // Example from README: Auto-detect provider
  const adapter = createStorageAdapter({ type: "auto" });
  assertExists(adapter);
  
  // Example from README: List objects
  const objects = await adapter.list();
  assertExists(objects.objects);
  
  // Example from README: Upload file
  const uploadResult = await adapter.upload(
    "readme-test.txt",
    "README example content"
  );
  assertExists(uploadResult.etag);
});

// Skip tests for features that require actual npm publishing
Deno.test.skip("Package can be installed via npm", () => {
  // Skip reason: Package needs to be published to npm first
  // This would test: npm install @storage/s3-adapter
});

Deno.test.skip("Package works in Node.js environment", () => {
  // Skip reason: Requires Node.js runtime and build process
  // This would test Node.js compatibility layer
});

Deno.test.skip("Package can be imported in browser environment", () => {
  // Skip reason: Requires browser build and testing environment
  // This would test ES modules in browser
});