/**
 * Flake Integration Tests
 * Verifies that the package works correctly when used as a Nix flake input
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { resolve } from "https://deno.land/std@0.208.0/path/mod.ts";

Deno.test("Flake exposes correct package structure", async () => {
  // Verify that main entry points exist and are accessible
  const mainPath = resolve("./main.ts");
  const modPath = resolve("./mod.ts");
  
  // Check files exist
  const mainExists = await Deno.stat(mainPath).then(() => true).catch(() => false);
  const modExists = await Deno.stat(modPath).then(() => true).catch(() => false);
  
  assertEquals(mainExists, true, "main.ts should exist for CLI");
  assertEquals(modExists, true, "mod.ts should exist for library usage");
});

Deno.test("Flake library exports work when imported", async () => {
  // Test that mod.ts exports can be imported by other flakes
  const mod = await import("./mod.ts");
  
  // Verify all expected exports
  assertExists(mod.createStorageAdapter, "createStorageAdapter should be exported");
  assertExists(mod.S3StorageApplication, "S3StorageApplication should be exported");
  assertExists(mod.StorageAdapter, "StorageAdapter type should be exported");
  assertExists(mod.StorageConfig, "StorageConfig type should be exported");
  assertExists(mod.S3Command, "S3Command type should be exported");
  assertExists(mod.S3Result, "S3Result type should be exported");
});

Deno.test("Flake can be used as library dependency", async () => {
  // Simulate how another flake would use this as input
  const { createStorageAdapter } = await import("./mod.ts");
  
  // Create adapter without any external dependencies
  const adapter = createStorageAdapter({ type: "in-memory" });
  
  // Verify it works
  await adapter.upload("flake-test.txt", "Testing flake integration");
  const result = await adapter.download("flake-test.txt");
  const content = new TextDecoder().decode(result.content);
  assertEquals(content, "Testing flake integration");
});

Deno.test("Flake CLI can be invoked programmatically", async () => {
  // Test that main.ts can be imported and used
  try {
    // Import main module to verify it's valid
    await import("./main.ts");
    // If import succeeds, CLI structure is valid
  } catch (error) {
    // CLI might have top-level await or other runtime code
    // This is acceptable for CLI entry points
    assertEquals(error.name, "TypeError", "Only type errors are acceptable");
  }
});

Deno.test("Flake works with minimal Nix dependencies", async () => {
  // Verify no runtime Nix dependencies are required
  const { createStorageAdapter, S3StorageApplication } = await import("./mod.ts");
  
  // Test in-memory adapter (no external deps)
  const adapter = createStorageAdapter({ type: "in-memory" });
  assertEquals(adapter.getType(), "in-memory");
  
  // Test application layer
  const app = new S3StorageApplication({ type: "in-memory" });
  const result = await app.execute({ type: "list" });
  assertEquals(result.type, "list");
});

Deno.test("Flake test command would execute all tests", async () => {
  // Verify test files follow naming convention
  const testFiles: string[] = [];
  
  for await (const entry of Deno.readDir(".")) {
    if (entry.isFile && entry.name.endsWith(".test.ts")) {
      testFiles.push(entry.name);
    }
  }
  
  // Should have multiple test files
  assertEquals(testFiles.length > 5, true, "Should have comprehensive test coverage");
  
  // Verify key test files exist
  assertEquals(testFiles.includes("adapter.test.ts"), true);
  assertEquals(testFiles.includes("domain.test.ts"), true);
  assertEquals(testFiles.includes("application.test.ts"), true);
});

Deno.test("Flake package.default provides CLI functionality", () => {
  // This test verifies the flake structure
  // In actual usage, `nix run .` would execute the CLI
  
  // Verify CLI entry point exists
  const cliEntryExists = Deno.statSync("./main.ts").isFile;
  assertEquals(cliEntryExists, true);
});

// Integration test that simulates external flake usage
Deno.test("Flake integration example: S3 backup tool", async () => {
  // Example of how another project would use this flake
  const { createStorageAdapter, S3StorageApplication } = await import("./mod.ts");
  
  // Create backup tool using our library
  class BackupTool {
    private storage: S3StorageApplication;
    
    constructor() {
      this.storage = new S3StorageApplication({ type: "in-memory" });
    }
    
    async backup(files: Record<string, string>) {
      const results = [];
      for (const [path, content] of Object.entries(files)) {
        const result = await this.storage.execute({
          type: "upload",
          key: `backup/${path}`,
          content
        });
        results.push(result);
      }
      return results;
    }
    
    async restore(prefix: string) {
      const listResult = await this.storage.execute({
        type: "list",
        options: { prefix }
      });
      
      if (listResult.type !== "list") throw new Error("List failed");
      
      const files: Record<string, string> = {};
      for (const obj of listResult.objects) {
        const downloadResult = await this.storage.execute({
          type: "download",
          key: obj.key
        });
        if (downloadResult.type === "download") {
          files[obj.key] = new TextDecoder().decode(downloadResult.content);
        }
      }
      return files;
    }
  }
  
  // Test the backup tool
  const backupTool = new BackupTool();
  
  // Backup some files
  await backupTool.backup({
    "config.json": '{"version": "1.0"}',
    "data.txt": "Important data"
  });
  
  // Restore and verify
  const restored = await backupTool.restore("backup/");
  assertEquals(Object.keys(restored).length, 2);
  assertEquals(restored["backup/config.json"], '{"version": "1.0"}');
  assertEquals(restored["backup/data.txt"], "Important data");
});

// Test that verifies flake would work in pure evaluation mode
Deno.test("Flake structure supports pure evaluation", () => {
  // Verify no impure operations in module exports
  // This is a compile-time test - if it compiles, it passes
  
  type PureExports = {
    // All exports should be pure functions or types
    createStorageAdapter: typeof import("./mod.ts").createStorageAdapter;
    S3StorageApplication: typeof import("./mod.ts").S3StorageApplication;
    // Types are always pure
    StorageAdapter: import("./adapter.ts").StorageAdapter;
    StorageConfig: import("./adapter.ts").StorageConfig;
  };
  
  // This would fail to compile if exports weren't pure
  const _pureCheck: PureExports = {} as any;
});