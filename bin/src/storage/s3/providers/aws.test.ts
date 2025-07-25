/**
 * Tests for AWS S3 Storage Adapter
 * Uses the common test helpers to ensure consistent behavior
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createStorageAdapter } from "../adapter.ts";
import type { StorageConfig } from "../adapter.ts";
import { testStorageAdapter, verifyObjectSorting, verifyOverwriteBehavior } from "./test-helpers.ts";

// AWS S3 configuration for testing
const awsS3Config: StorageConfig = {
  type: "s3",
  endpoint: "https://s3.amazonaws.com",
  region: "us-east-1",
  accessKeyId: "test-access-key",
  secretAccessKey: "test-secret-key",
  bucket: "test-bucket"
};

// Test: AWS S3 adapter creation
Deno.test("AWS S3: adapter creation and type detection", () => {
  const adapter = createStorageAdapter(awsS3Config);
  assertEquals(adapter.getType(), "s3");
});

// Test: Common storage adapter behavior
Deno.test("AWS S3: common storage adapter tests", async () => {
  const adapter = createStorageAdapter(awsS3Config);
  await testStorageAdapter(adapter, "AWS S3");
});

// Test: AWS S3 specific - object sorting
Deno.test("AWS S3: verifies object sorting", async () => {
  const adapter = createStorageAdapter(awsS3Config);
  await verifyObjectSorting(adapter);
});

// Test: AWS S3 specific - overwrite behavior
Deno.test("AWS S3: verifies overwrite behavior", async () => {
  const adapter = createStorageAdapter(awsS3Config);
  await verifyOverwriteBehavior(adapter);
});

// Test: AWS S3 specific - region configurations
Deno.test("AWS S3: supports various region configurations", () => {
  const regions = ["us-west-2", "eu-west-1", "ap-northeast-1"];
  
  for (const region of regions) {
    const config: StorageConfig = {
      ...awsS3Config,
      region
    };
    const adapter = createStorageAdapter(config);
    assertEquals(adapter.getType(), "s3");
  }
});

// Test: AWS S3 specific - endpoint variations
Deno.test("AWS S3: handles various endpoint formats", () => {
  const endpoints = [
    "https://s3.amazonaws.com",
    "https://s3.us-east-1.amazonaws.com",
    "https://s3-us-west-2.amazonaws.com"
  ];
  
  for (const endpoint of endpoints) {
    const config: StorageConfig = {
      ...awsS3Config,
      endpoint
    };
    const adapter = createStorageAdapter(config);
    assertEquals(adapter.getType(), "s3");
  }
});