/**
 * Tests for In-Memory Storage Adapter
 * These tests verify the behavior of the default in-memory storage implementation
 * They serve as executable specifications for how storage should work
 */

import { assertEquals, assertExists, assertRejects } from "https://deno.land/std@0.208.0/assert/mod.ts";
import { createStorageAdapter } from "./adapter.ts";

// Test: In-memory adapter should list objects with proper filtering
Deno.test("in-memory adapter lists objects with prefix filtering", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload test objects
  await adapter.upload("photos/summer/beach.jpg", "beach photo");
  await adapter.upload("photos/summer/sunset.jpg", "sunset photo");
  await adapter.upload("photos/winter/snow.jpg", "snow photo");
  await adapter.upload("documents/report.pdf", "report content");
  
  // Test 1: List all objects
  const allObjects = await adapter.list();
  assertEquals(allObjects.objects.length, 4);
  assertEquals(allObjects.isTruncated, false);
  
  // Test 2: List with prefix
  const summerPhotos = await adapter.list({ prefix: "photos/summer/" });
  assertEquals(summerPhotos.objects.length, 2);
  assertEquals(summerPhotos.objects[0].key, "photos/summer/beach.jpg");
  assertEquals(summerPhotos.objects[1].key, "photos/summer/sunset.jpg");
  
  // Test 3: List with different prefix
  const winterPhotos = await adapter.list({ prefix: "photos/winter/" });
  assertEquals(winterPhotos.objects.length, 1);
  assertEquals(winterPhotos.objects[0].key, "photos/winter/snow.jpg");
  
  // Test 4: List with non-existent prefix
  const noMatch = await adapter.list({ prefix: "videos/" });
  assertEquals(noMatch.objects.length, 0);
  assertEquals(noMatch.isTruncated, false);
});

// Test: In-memory adapter should handle pagination correctly
Deno.test("in-memory adapter handles pagination with maxKeys", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload multiple objects
  for (let i = 0; i < 5; i++) {
    await adapter.upload(`file${i}.txt`, `content ${i}`);
  }
  
  // Test pagination
  const page1 = await adapter.list({ maxKeys: 2 });
  assertEquals(page1.objects.length, 2);
  assertEquals(page1.isTruncated, true);
  assertExists(page1.continuationToken);
  
  // Verify objects have required properties
  for (const obj of page1.objects) {
    assertExists(obj.key);
    assertExists(obj.lastModified);
    assertExists(obj.size);
    assertExists(obj.etag);
  }
});

// Test: In-memory adapter should track object metadata
Deno.test("in-memory adapter tracks object size and modification time", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  const beforeUpload = new Date();
  await adapter.upload("test.txt", "Hello, World!");
  const afterUpload = new Date();
  
  const result = await adapter.list();
  assertEquals(result.objects.length, 1);
  
  const obj = result.objects[0];
  assertEquals(obj.key, "test.txt");
  assertEquals(obj.size, 13); // "Hello, World!" is 13 bytes
  
  // Verify timestamp is reasonable
  const modified = obj.lastModified.getTime();
  assertEquals(modified >= beforeUpload.getTime(), true);
  assertEquals(modified <= afterUpload.getTime(), true);
});

// Test: List should return objects sorted by key
Deno.test("in-memory adapter returns objects sorted by key", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload in random order
  await adapter.upload("c.txt", "content c");
  await adapter.upload("a.txt", "content a");
  await adapter.upload("b.txt", "content b");
  
  const result = await adapter.list();
  const keys = result.objects.map(obj => obj.key);
  
  // Should be sorted alphabetically
  assertEquals(keys, ["a.txt", "b.txt", "c.txt"]);
});

// Test: Upload operations should handle different content types
Deno.test("in-memory adapter handles string and binary uploads", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Test string upload
  const textResult = await adapter.upload("text.txt", "Hello, World!");
  assertEquals(textResult.key, "text.txt");
  assertExists(textResult.etag);
  
  // Test binary upload
  const binaryData = new Uint8Array([0xFF, 0xD8, 0xFF, 0xE0]); // JPEG header
  const binaryResult = await adapter.upload("image.jpg", binaryData);
  assertEquals(binaryResult.key, "image.jpg");
  assertExists(binaryResult.etag);
  
  // Verify both exist
  const list = await adapter.list();
  assertEquals(list.objects.length, 2);
});

// Test: Upload should support content type and metadata
Deno.test("in-memory adapter stores content type and metadata", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  await adapter.upload("document.pdf", "PDF content", {
    contentType: "application/pdf",
    metadata: {
      author: "John Doe",
      version: "1.0"
    }
  });
  
  const downloadResult = await adapter.download("document.pdf");
  assertEquals(downloadResult.contentType, "application/pdf");
  assertEquals(downloadResult.metadata?.author, "John Doe");
  assertEquals(downloadResult.metadata?.version, "1.0");
});

// Test: Upload should overwrite existing objects
Deno.test("in-memory adapter overwrites existing objects on upload", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // First upload
  await adapter.upload("file.txt", "version 1");
  const firstInfo = await adapter.info("file.txt");
  const firstModified = firstInfo.lastModified;
  const firstEtag = (await adapter.list()).objects[0].etag;
  
  // Wait a bit to ensure different timestamp
  await new Promise(resolve => setTimeout(resolve, 10));
  
  // Second upload (overwrite)
  await adapter.upload("file.txt", "version 2");
  const secondInfo = await adapter.info("file.txt");
  const secondEtag = (await adapter.list()).objects[0].etag;
  
  // Verify overwrite
  const list = await adapter.list();
  assertEquals(list.objects.length, 1); // Still only one object
  
  const downloaded = await adapter.download("file.txt");
  const content = new TextDecoder().decode(downloaded.content);
  assertEquals(content, "version 2");
  
  // Verify metadata changed
  assertEquals(secondInfo.lastModified! > firstModified!, true);
  assertEquals(secondEtag !== firstEtag, true);
});

// Test: Upload should generate unique ETags
Deno.test("in-memory adapter generates unique ETags for different content", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  const result1 = await adapter.upload("file1.txt", "content A");
  const result2 = await adapter.upload("file2.txt", "content B");
  const result3 = await adapter.upload("file3.txt", "content A"); // Same content as file1
  
  // Different content should have different ETags
  assertEquals(result1.etag !== result2.etag, true);
  
  // Same content should have same ETag (content-based)
  assertEquals(result1.etag, result3.etag);
});

// Test: Download should retrieve uploaded content correctly
Deno.test("in-memory adapter downloads uploaded content", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload text
  const textContent = "Hello, Storage!";
  await adapter.upload("greeting.txt", textContent);
  
  // Download and verify
  const result = await adapter.download("greeting.txt");
  assertEquals(result.key, "greeting.txt");
  
  const downloadedText = new TextDecoder().decode(result.content);
  assertEquals(downloadedText, textContent);
});

// Test: Download should handle binary content
Deno.test("in-memory adapter downloads binary content correctly", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload binary data
  const binaryData = new Uint8Array([0x89, 0x50, 0x4E, 0x47]); // PNG header
  await adapter.upload("image.png", binaryData, {
    contentType: "image/png"
  });
  
  // Download and verify
  const result = await adapter.download("image.png");
  assertEquals(result.contentType, "image/png");
  assertEquals(result.content.length, 4);
  assertEquals(Array.from(result.content), [0x89, 0x50, 0x4E, 0x47]);
});

// Test: Download non-existent object should fail
Deno.test("in-memory adapter throws error when downloading non-existent object", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  await assertRejects(
    async () => await adapter.download("does-not-exist.txt"),
    Error,
    "Object not found: does-not-exist.txt"
  );
});

// Test: Delete operations
Deno.test("in-memory adapter deletes objects correctly", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Upload multiple objects
  await adapter.upload("file1.txt", "content 1");
  await adapter.upload("file2.txt", "content 2");
  await adapter.upload("file3.txt", "content 3");
  
  // Delete some objects
  const deleteResult = await adapter.delete(["file1.txt", "file3.txt", "non-existent.txt"]);
  
  // Verify delete results
  assertEquals(deleteResult.deleted.length, 2);
  assertEquals(deleteResult.deleted.includes("file1.txt"), true);
  assertEquals(deleteResult.deleted.includes("file3.txt"), true);
  
  assertEquals(deleteResult.errors.length, 1);
  assertEquals(deleteResult.errors[0].key, "non-existent.txt");
  assertEquals(deleteResult.errors[0].error, "Object not found");
  
  // Verify only file2.txt remains
  const list = await adapter.list();
  assertEquals(list.objects.length, 1);
  assertEquals(list.objects[0].key, "file2.txt");
});

// Test: Info operation
Deno.test("in-memory adapter provides accurate object info", async () => {
  const adapter = createStorageAdapter({ type: "auto" });
  
  // Test non-existent object
  const notFound = await adapter.info("missing.txt");
  assertEquals(notFound.exists, false);
  assertEquals(notFound.key, "missing.txt");
  
  // Upload an object
  const content = "Test content for info";
  await adapter.upload("info-test.txt", content, {
    contentType: "text/plain",
    metadata: { 
      custom: "value",
      tag: "test" 
    }
  });
  
  // Get info
  const info = await adapter.info("info-test.txt");
  assertEquals(info.exists, true);
  assertEquals(info.key, "info-test.txt");
  assertEquals(info.size, 21); // "Test content for info" is 21 bytes
  assertEquals(info.contentType, "text/plain");
  assertExists(info.lastModified);
  assertEquals(info.metadata?.custom, "value");
  assertEquals(info.metadata?.tag, "test");
});