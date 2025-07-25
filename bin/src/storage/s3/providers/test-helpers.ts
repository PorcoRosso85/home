/**
 * Common test helpers for storage adapter testing
 * These utilities help ensure consistent testing across all storage implementations
 */

import { assertEquals, assertExists, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type { StorageAdapter } from "../adapter.ts";

/**
 * Common test data used across adapter tests
 */
export const TEST_DATA = {
  // Text content
  textFile: {
    key: "test-file.txt",
    content: "Hello, Storage Adapter!",
    contentType: "text/plain"
  },
  
  // Binary content (PNG header)
  binaryFile: {
    key: "test-image.png",
    content: new Uint8Array([0x89, 0x50, 0x4E, 0x47]),
    contentType: "image/png"
  },
  
  // Hierarchical keys for prefix testing
  hierarchicalFiles: [
    { key: "photos/summer/beach.jpg", content: "beach photo" },
    { key: "photos/summer/sunset.jpg", content: "sunset photo" },
    { key: "photos/winter/snow.jpg", content: "snow photo" },
    { key: "documents/report.pdf", content: "report content" }
  ],
  
  // Invalid keys for validation testing
  invalidKeys: [
    { key: "invalid\0key.txt", error: "invalid characters" },
    { key: "invalid\x01key.txt", error: "invalid characters" },
    { key: "a".repeat(1025), error: "exceeds maximum length" }
  ]
};

/**
 * Test suite for verifying storage adapter behavior
 * This function runs a comprehensive set of tests against any StorageAdapter implementation
 * 
 * @param adapter - The storage adapter to test
 * @param adapterName - Name of the adapter for test descriptions
 */
export async function testStorageAdapter(adapter: StorageAdapter, adapterName: string) {
  // Test 1: Upload and download basic functionality
  await testUploadDownload(adapter, adapterName);
  
  // Test 2: List operations with filtering and pagination
  await testListOperations(adapter, adapterName);
  
  // Test 3: Delete operations
  await testDeleteOperations(adapter, adapterName);
  
  // Test 4: Info operations
  await testInfoOperations(adapter, adapterName);
  
  // Test 5: Key validation
  await testKeyValidation(adapter, adapterName);
  
  // Test 6: Metadata support
  await testMetadataSupport(adapter, adapterName);
}

/**
 * Test upload and download operations
 */
async function testUploadDownload(adapter: StorageAdapter, adapterName: string) {
  // Test string upload/download
  const uploadResult = await adapter.upload(TEST_DATA.textFile.key, TEST_DATA.textFile.content);
  assertEquals(uploadResult.key, TEST_DATA.textFile.key);
  assertExists(uploadResult.etag);
  
  const downloadResult = await adapter.download(TEST_DATA.textFile.key);
  assertEquals(downloadResult.key, TEST_DATA.textFile.key);
  const content = new TextDecoder().decode(downloadResult.content);
  assertEquals(content, TEST_DATA.textFile.content);
  
  // Test binary upload/download
  const binaryUpload = await adapter.upload(
    TEST_DATA.binaryFile.key, 
    TEST_DATA.binaryFile.content,
    { contentType: TEST_DATA.binaryFile.contentType }
  );
  assertEquals(binaryUpload.key, TEST_DATA.binaryFile.key);
  
  const binaryDownload = await adapter.download(TEST_DATA.binaryFile.key);
  assertEquals(binaryDownload.contentType, TEST_DATA.binaryFile.contentType);
  assertEquals(Array.from(binaryDownload.content), Array.from(TEST_DATA.binaryFile.content));
  
  // Cleanup
  await adapter.delete([TEST_DATA.textFile.key, TEST_DATA.binaryFile.key]);
}

/**
 * Test list operations with prefix filtering and pagination
 */
async function testListOperations(adapter: StorageAdapter, adapterName: string) {
  // Upload hierarchical test files
  for (const file of TEST_DATA.hierarchicalFiles) {
    await adapter.upload(file.key, file.content);
  }
  
  // Test listing all objects
  const allObjects = await adapter.list();
  assertEquals(allObjects.objects.length >= TEST_DATA.hierarchicalFiles.length, true);
  assertEquals(allObjects.isTruncated, false);
  
  // Test prefix filtering
  const summerPhotos = await adapter.list({ prefix: "photos/summer/" });
  assertEquals(summerPhotos.objects.length, 2);
  const summerKeys = summerPhotos.objects.map(obj => obj.key);
  assertEquals(summerKeys.includes("photos/summer/beach.jpg"), true);
  assertEquals(summerKeys.includes("photos/summer/sunset.jpg"), true);
  
  // Test pagination
  const page1 = await adapter.list({ maxKeys: 2 });
  assertEquals(page1.objects.length <= 2, true);
  if (page1.objects.length === 2 && allObjects.objects.length > 2) {
    assertEquals(page1.isTruncated, true);
    assertExists(page1.continuationToken);
  }
  
  // Verify object properties
  for (const obj of allObjects.objects) {
    assertExists(obj.key);
    assertExists(obj.lastModified);
    assertExists(obj.size);
    assertExists(obj.etag);
  }
  
  // Cleanup
  const keysToDelete = TEST_DATA.hierarchicalFiles.map(f => f.key);
  await adapter.delete(keysToDelete);
}

/**
 * Test delete operations
 */
async function testDeleteOperations(adapter: StorageAdapter, adapterName: string) {
  // Upload test files
  const testKeys = ["delete-test-1.txt", "delete-test-2.txt", "delete-test-3.txt"];
  for (const key of testKeys) {
    await adapter.upload(key, "content to delete");
  }
  
  // Delete some files (including non-existent)
  const deleteResult = await adapter.delete([
    testKeys[0],
    testKeys[2],
    "non-existent-file.txt"
  ]);
  
  // Verify delete results
  assertEquals(deleteResult.deleted.length, 2);
  assertEquals(deleteResult.deleted.includes(testKeys[0]), true);
  assertEquals(deleteResult.deleted.includes(testKeys[2]), true);
  
  assertEquals(deleteResult.errors.length, 1);
  assertEquals(deleteResult.errors[0].key, "non-existent-file.txt");
  
  // Verify only middle file remains
  const remaining = await adapter.list();
  const remainingKeys = remaining.objects.map(obj => obj.key);
  assertEquals(remainingKeys.includes(testKeys[1]), true);
  assertEquals(remainingKeys.includes(testKeys[0]), false);
  assertEquals(remainingKeys.includes(testKeys[2]), false);
  
  // Cleanup
  await adapter.delete([testKeys[1]]);
}

/**
 * Test info operations
 */
async function testInfoOperations(adapter: StorageAdapter, adapterName: string) {
  // Test non-existent object
  const notFound = await adapter.info("non-existent.txt");
  assertEquals(notFound.exists, false);
  assertEquals(notFound.key, "non-existent.txt");
  
  // Upload test object with metadata
  const testKey = "info-test.txt";
  const testContent = "Test content for info";
  await adapter.upload(testKey, testContent, {
    contentType: "text/plain",
    metadata: {
      author: "Test Suite",
      version: "1.0"
    }
  });
  
  // Get info
  const info = await adapter.info(testKey);
  assertEquals(info.exists, true);
  assertEquals(info.key, testKey);
  assertEquals(info.size, testContent.length);
  assertEquals(info.contentType, "text/plain");
  assertExists(info.lastModified);
  assertEquals(info.metadata?.author, "Test Suite");
  assertEquals(info.metadata?.version, "1.0");
  
  // Cleanup
  await adapter.delete([testKey]);
}

/**
 * Test key validation
 */
async function testKeyValidation(adapter: StorageAdapter, adapterName: string) {
  // Test invalid keys
  for (const { key, error } of TEST_DATA.invalidKeys) {
    await assertRejects(
      async () => await adapter.upload(key, "content"),
      Error,
      error
    );
    
    await assertRejects(
      async () => await adapter.download(key),
      Error,
      error
    );
    
    await assertRejects(
      async () => await adapter.info(key),
      Error,
      error
    );
  }
  
  // Test delete with invalid keys
  const deleteResult = await adapter.delete([TEST_DATA.invalidKeys[0].key]);
  assertEquals(deleteResult.deleted.length, 0);
  assertEquals(deleteResult.errors.length, 1);
  assertEquals(deleteResult.errors[0].key, TEST_DATA.invalidKeys[0].key);
}

/**
 * Test metadata support
 */
async function testMetadataSupport(adapter: StorageAdapter, adapterName: string) {
  const testKey = "metadata-test.json";
  const testMetadata = {
    version: "2.0",
    environment: "test",
    timestamp: new Date().toISOString()
  };
  
  // Upload with metadata
  await adapter.upload(testKey, '{"data": "test"}', {
    contentType: "application/json",
    metadata: testMetadata
  });
  
  // Download and verify metadata
  const downloadResult = await adapter.download(testKey);
  assertEquals(downloadResult.contentType, "application/json");
  assertEquals(downloadResult.metadata?.version, testMetadata.version);
  assertEquals(downloadResult.metadata?.environment, testMetadata.environment);
  assertEquals(downloadResult.metadata?.timestamp, testMetadata.timestamp);
  
  // Cleanup
  await adapter.delete([testKey]);
}

/**
 * Helper to create test content of specified size
 */
export function createTestContent(sizeInBytes: number): Uint8Array {
  const content = new Uint8Array(sizeInBytes);
  // Fill with some pattern to avoid all zeros
  for (let i = 0; i < sizeInBytes; i++) {
    content[i] = i % 256;
  }
  return content;
}

/**
 * Helper to verify object sorting
 */
export async function verifyObjectSorting(adapter: StorageAdapter) {
  const unsortedKeys = ["c.txt", "a.txt", "b.txt"];
  
  // Upload in unsorted order
  for (const key of unsortedKeys) {
    await adapter.upload(key, `content for ${key}`);
  }
  
  // List and verify sorting
  const result = await adapter.list();
  const listedKeys = result.objects
    .filter(obj => unsortedKeys.includes(obj.key))
    .map(obj => obj.key);
  
  assertEquals(listedKeys, ["a.txt", "b.txt", "c.txt"]);
  
  // Cleanup
  await adapter.delete(unsortedKeys);
}

/**
 * Helper to test overwrite behavior
 */
export async function verifyOverwriteBehavior(adapter: StorageAdapter) {
  const testKey = "overwrite-test.txt";
  
  // First upload
  await adapter.upload(testKey, "version 1");
  const firstInfo = await adapter.info(testKey);
  
  // Wait to ensure different timestamp
  await new Promise(resolve => setTimeout(resolve, 10));
  
  // Overwrite
  await adapter.upload(testKey, "version 2");
  const secondInfo = await adapter.info(testKey);
  
  // Verify overwrite
  const downloaded = await adapter.download(testKey);
  const content = new TextDecoder().decode(downloaded.content);
  assertEquals(content, "version 2");
  
  // Verify metadata changed
  if (firstInfo.lastModified && secondInfo.lastModified) {
    assertEquals(secondInfo.lastModified > firstInfo.lastModified, true);
  }
  
  // Cleanup
  await adapter.delete([testKey]);
}