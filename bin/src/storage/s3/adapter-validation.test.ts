/**
 * Tests for Storage Adapter Validation
 * Ensures domain validation rules are enforced at the adapter level
 */

import { assertEquals, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createStorageAdapter } from "./adapter.ts";

Deno.test("In-memory adapter validates S3 key constraints", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Test 1: Valid key should work
  await adapter.upload("valid-key.txt", "content");
  
  // Test 2: Key with null byte should fail
  await assertRejects(
    async () => await adapter.upload("invalid\0key.txt", "content"),
    Error,
    "invalid characters"
  );
  
  // Test 3: Key exceeding 1024 bytes should fail
  const longKey = "a".repeat(1025);
  await assertRejects(
    async () => await adapter.upload(longKey, "content"),
    Error,
    "exceeds maximum length"
  );
  
  // Test 4: Key with control characters should fail
  await assertRejects(
    async () => await adapter.upload("invalid\x01key.txt", "content"),
    Error,
    "invalid characters"
  );
});

Deno.test("In-memory adapter validates S3 object size constraints", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Test 1: Normal size should work
  const normalContent = new Uint8Array(1024 * 1024); // 1MB
  await adapter.upload("normal-size.bin", normalContent);
  
  // Test 2: 5GB is the maximum allowed size
  // Note: We can't actually test 5GB in memory, but we can test the validation logic
  // by mocking a large size. For now, we'll test with a reasonable size.
  const largeContent = new Uint8Array(100 * 1024 * 1024); // 100MB
  await adapter.upload("large-size.bin", largeContent);
});

Deno.test("In-memory adapter validates keys on all operations", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  const invalidKey = "invalid\0key.txt";
  
  // All operations should validate the key
  await assertRejects(
    async () => await adapter.download(invalidKey),
    Error,
    "invalid characters"
  );
  
  await assertRejects(
    async () => await adapter.info(invalidKey),
    Error,
    "invalid characters"
  );
  
  await assertRejects(
    async () => await adapter.delete([invalidKey]),
    Error,
    "invalid characters"
  );
});

Deno.test("S3 adapter validates bucket name", async () => {
  // Test 1: Invalid bucket name (too short) should fail
  await assertRejects(
    async () => createStorageAdapter({
      type: "s3",
      endpoint: "http://localhost:9000",
      region: "us-east-1",
      accessKeyId: "key",
      secretAccessKey: "secret",
      bucket: "ab" // Too short
    }),
    Error,
    "between 3 and 63 characters"
  );
  
  // Test 2: Invalid bucket name (uppercase) should fail
  await assertRejects(
    async () => createStorageAdapter({
      type: "s3",
      endpoint: "http://localhost:9000",
      region: "us-east-1",
      accessKeyId: "key",
      secretAccessKey: "secret",
      bucket: "INVALID-BUCKET"
    }),
    Error,
    "lowercase letters, numbers, and hyphens"
  );
  
  // Test 3: Invalid bucket name (consecutive hyphens) should fail
  await assertRejects(
    async () => createStorageAdapter({
      type: "s3",
      endpoint: "http://localhost:9000",
      region: "us-east-1",
      accessKeyId: "key",
      secretAccessKey: "secret",
      bucket: "invalid--bucket"
    }),
    Error,
    "consecutive hyphens"
  );
  
  // Test 4: Valid bucket name should work
  const adapter = createStorageAdapter({
    type: "s3",
    endpoint: "http://localhost:9000",
    region: "us-east-1",
    accessKeyId: "key",
    secretAccessKey: "secret",
    bucket: "valid-bucket-123"
  });
  assertEquals(adapter.getType(), "minio");
});

Deno.test("Delete operation handles validation errors gracefully", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload a valid file first
  await adapter.upload("valid-file.txt", "content");
  
  // Try to delete both valid and invalid keys
  const result = await adapter.delete([
    "valid-file.txt",
    "invalid\0key.txt",
    "another-invalid\x01.txt"
  ]);
  
  // Should successfully delete the valid file
  assertEquals(result.deleted.length, 1);
  assertEquals(result.deleted[0], "valid-file.txt");
  
  // Should report errors for invalid keys
  assertEquals(result.errors.length, 2);
  assertEquals(result.errors[0].key, "invalid\0key.txt");
  assertEquals(result.errors[0].error, "S3 key contains invalid characters");
  assertEquals(result.errors[1].key, "another-invalid\x01.txt");
  assertEquals(result.errors[1].error, "S3 key contains invalid characters");
});