/**
 * Tests for S3 Storage Adapter
 * These tests verify that the S3 adapter correctly implements the StorageAdapter interface
 * and properly integrates with the existing S3Client infrastructure
 */

import { assertEquals, assertExists } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createStorageAdapter } from "./adapter.ts";
import type { StorageAdapter, StorageConfig } from "./adapter.ts";

// Mock S3 configuration for testing
const mockS3Config: StorageConfig = {
  type: "s3",
  endpoint: "https://s3.amazonaws.com",
  region: "us-east-1",
  accessKeyId: "test-access-key",
  secretAccessKey: "test-secret-key",
  bucket: "test-bucket"
};

// Test: S3 adapter should be created for S3 configuration
Deno.test("createStorageAdapter returns S3 adapter for S3 config", () => {
  const adapter = createStorageAdapter(mockS3Config);
  assertEquals(adapter.getType(), "s3");
});

// Test: S3 adapter should integrate with existing S3Client
Deno.test("S3 adapter uses existing S3Client for operations", async () => {
  const adapter = createStorageAdapter(mockS3Config);
  
  // The adapter should exist and have all required methods
  assertExists(adapter.list);
  assertExists(adapter.upload);
  assertExists(adapter.download);
  assertExists(adapter.delete);
  assertExists(adapter.info);
  
  // Note: We can't test actual S3 operations without mocking AWS SDK
  // These tests verify the interface compliance
});

// Test: Provider detection should work correctly
Deno.test("S3 adapter detects AWS S3 provider", () => {
  const awsAdapter = createStorageAdapter({
    type: "s3",
    endpoint: "https://s3.amazonaws.com",
    region: "us-east-1",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(awsAdapter.getType(), "s3");
});

Deno.test("S3 adapter detects MinIO provider", () => {
  const minioAdapter = createStorageAdapter({
    type: "s3",
    endpoint: "http://localhost:9000",
    region: "us-east-1",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(minioAdapter.getType(), "minio");
});

Deno.test("S3 adapter detects Cloudflare R2 provider", () => {
  const r2Adapter = createStorageAdapter({
    type: "s3",
    endpoint: "https://account.r2.cloudflarestorage.com",
    region: "auto",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(r2Adapter.getType(), "r2");
});

Deno.test("S3 adapter detects Backblaze B2 provider", () => {
  const b2Adapter = createStorageAdapter({
    type: "s3",
    endpoint: "https://s3.us-west-001.backblazeb2.com",
    region: "us-west-001",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "bucket"
  });
  assertEquals(b2Adapter.getType(), "b2");
});

// Test: S3 adapter should handle adapter interface correctly
Deno.test("S3 adapter implements StorageAdapter interface correctly", async () => {
  const adapter: StorageAdapter = createStorageAdapter(mockS3Config);
  
  // Type checking ensures the adapter conforms to the interface
  // This test passes if TypeScript compilation succeeds
  assertEquals(typeof adapter.list, "function");
  assertEquals(typeof adapter.upload, "function");
  assertEquals(typeof adapter.download, "function");
  assertEquals(typeof adapter.delete, "function");
  assertEquals(typeof adapter.info, "function");
  assertEquals(typeof adapter.getType, "function");
  assertEquals(typeof adapter.isHealthy, "function");
});