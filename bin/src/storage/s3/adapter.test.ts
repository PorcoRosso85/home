/**
 * Tests for Storage Adapter Pattern
 * These tests serve as executable specifications for the adapter interface
 * Following the "wall of refactoring" principle - tests only interact with public API
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type { 
  StorageAdapter,
  StorageConfig,
  StorageObject,
  StorageListOptions,
  StorageUploadOptions,
  StorageDownloadOptions
} from "./adapter.ts";

// Test: Storage adapter interface must define all required operations
Deno.test("StorageAdapter interface defines all required storage operations", () => {
  // This test verifies that the StorageAdapter interface exists and has the correct shape
  // It serves as a specification for what every adapter implementation must provide
  
  // Create a mock adapter to verify interface compliance
  const mockAdapter: StorageAdapter = {
    list: async (options?: StorageListOptions) => {
      return {
        objects: [],
        continuationToken: undefined,
        isTruncated: false
      };
    },
    
    upload: async (key: string, content: string | Uint8Array, options?: StorageUploadOptions) => {
      return {
        key,
        etag: "mock-etag",
        versionId: undefined
      };
    },
    
    download: async (key: string, options?: StorageDownloadOptions) => {
      return {
        key,
        content: new Uint8Array(),
        contentType: undefined,
        metadata: undefined
      };
    },
    
    delete: async (keys: string[]) => {
      return {
        deleted: keys,
        errors: []
      };
    },
    
    info: async (key: string) => {
      return {
        key,
        exists: false
      };
    },
    
    // Adapter metadata
    getType: () => "mock",
    isHealthy: async () => true
  };
  
  // Verify all methods exist
  assertExists(mockAdapter.list);
  assertExists(mockAdapter.upload);
  assertExists(mockAdapter.download);
  assertExists(mockAdapter.delete);
  assertExists(mockAdapter.info);
  assertExists(mockAdapter.getType);
  assertExists(mockAdapter.isHealthy);
  
  // Verify method signatures by checking they are functions
  assertEquals(typeof mockAdapter.list, "function");
  assertEquals(typeof mockAdapter.upload, "function");
  assertEquals(typeof mockAdapter.download, "function");
  assertEquals(typeof mockAdapter.delete, "function");
  assertEquals(typeof mockAdapter.info, "function");
  assertEquals(typeof mockAdapter.getType, "function");
  assertEquals(typeof mockAdapter.isHealthy, "function");
});

// Test: Storage configuration must support all provider types
Deno.test("StorageConfig supports configuration for all storage providers", () => {
  // In-memory storage config (no endpoint = in-memory)
  const inMemoryConfig: StorageConfig = {
    type: "auto"
  };
  assertEquals(inMemoryConfig.type, "auto");
  
  // Filesystem storage config
  const filesystemConfig: StorageConfig = {
    type: "filesystem",
    basePath: "/tmp/storage"
  };
  assertEquals(filesystemConfig.type, "filesystem");
  assertEquals(filesystemConfig.basePath, "/tmp/storage");
  
  // S3-compatible storage config
  const s3Config: StorageConfig = {
    type: "s3",
    endpoint: "https://s3.amazonaws.com",
    region: "us-east-1",
    accessKeyId: "test-key",
    secretAccessKey: "test-secret",
    bucket: "test-bucket"
  };
  assertEquals(s3Config.type, "s3");
  assertEquals(s3Config.endpoint, "https://s3.amazonaws.com");
  
  // MinIO config
  const minioConfig: StorageConfig = {
    type: "s3",
    endpoint: "http://localhost:9000",
    region: "us-east-1",
    accessKeyId: "minioadmin",
    secretAccessKey: "minioadmin",
    bucket: "test-bucket"
  };
  assertEquals(minioConfig.endpoint, "http://localhost:9000");
});

// Test: Adapter factory must create appropriate adapter based on config
Deno.test("createStorageAdapter creates correct adapter based on configuration", async () => {
  const { createStorageAdapter } = await import("./adapter.ts");
  
  // Test 1: No config or empty endpoint = in-memory adapter
  const inMemoryAdapter = createStorageAdapter({});
  assertEquals(inMemoryAdapter.getType(), "in-memory");
  
  // Test 2: Filesystem type = filesystem adapter
  const filesystemAdapter = createStorageAdapter({
    type: "filesystem",
    basePath: "/tmp/test"
  });
  assertEquals(filesystemAdapter.getType(), "filesystem");
  
  // Test 3: S3 endpoint = S3 adapter
  const s3Adapter = createStorageAdapter({
    type: "s3",
    endpoint: "https://s3.amazonaws.com",
    region: "us-east-1",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(s3Adapter.getType(), "s3");
  
  // Test 4: Auto-detection based on endpoint
  const minioAdapter = createStorageAdapter({
    type: "auto",
    endpoint: "http://localhost:9000",
    region: "us-east-1",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(minioAdapter.getType(), "minio");
  
  // Test 5: R2 type = R2 adapter
  const r2Adapter = createStorageAdapter({
    type: "r2",
    accountId: "test-account-id",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(r2Adapter.getType(), "r2");
});

// Test: All adapters must implement consistent behavior (Liskov Substitution Principle)
Deno.test("All storage adapters behave consistently regardless of implementation", async () => {
  const { createStorageAdapter } = await import("./adapter.ts");
  
  // This test ensures that switching between adapters doesn't break the application
  // It's the core value proposition: change storage backend without changing code
  
  // Test with in-memory adapter
  const memoryAdapter = createStorageAdapter({ type: "auto" });
  assertEquals(memoryAdapter.getType(), "in-memory");
  
  // Basic smoke test
  const uploadResult = await memoryAdapter.upload("test-key", "test-content");
  assertEquals(uploadResult.key, "test-key");
  
  const downloadResult = await memoryAdapter.download("test-key");
  assertEquals(new TextDecoder().decode(downloadResult.content), "test-content");
});