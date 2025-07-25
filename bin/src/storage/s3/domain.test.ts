/**
 * Tests for domain types and logic
 */

import { assertEquals } from "https://deno.land/std@0.208.0/assert/mod.ts";
import type {
  S3Command,
  S3Result,
  ListCommand,
  UploadCommand,
  DownloadCommand,
  DeleteCommand,
  InfoCommand,
  HelpCommand,
} from "./domain.ts";

Deno.test("S3Command types should be correctly typed", () => {
  // Test ListCommand
  const listCmd: ListCommand = {
    action: "list",
    prefix: "test/",
    maxKeys: 10,
  };
  assertEquals(listCmd.action, "list");

  // Test UploadCommand
  const uploadCmd: UploadCommand = {
    action: "upload",
    key: "test.txt",
    content: "Hello, World!",
    contentType: "text/plain",
  };
  assertEquals(uploadCmd.action, "upload");

  // Test DownloadCommand
  const downloadCmd: DownloadCommand = {
    action: "download",
    key: "test.txt",
    outputPath: "./test.txt",
  };
  assertEquals(downloadCmd.action, "download");

  // Test DeleteCommand
  const deleteCmd: DeleteCommand = {
    action: "delete",
    keys: ["test1.txt", "test2.txt"],
  };
  assertEquals(deleteCmd.action, "delete");

  // Test InfoCommand
  const infoCmd: InfoCommand = {
    action: "info",
    key: "test.txt",
  };
  assertEquals(infoCmd.action, "info");

  // Test HelpCommand
  const helpCmd: HelpCommand = {
    action: "help",
  };
  assertEquals(helpCmd.action, "help");
});

Deno.test("S3Result types should handle all response cases", () => {
  // Test ListResult
  const listResult: S3Result = {
    type: "list",
    objects: [{
      key: "test.txt",
      lastModified: new Date(),
      size: 1024,
    }],
    isTruncated: false,
  };
  assertEquals(listResult.type, "list");

  // Test UploadResult
  const uploadResult: S3Result = {
    type: "upload",
    key: "test.txt",
    etag: "abc123",
  };
  assertEquals(uploadResult.type, "upload");

  // Test DownloadResult
  const downloadResult: S3Result = {
    type: "download",
    key: "test.txt",
    content: "Hello, World!",
  };
  assertEquals(downloadResult.type, "download");

  // Test DeleteResult
  const deleteResult: S3Result = {
    type: "delete",
    deleted: ["test1.txt"],
    errors: [{
      key: "test2.txt",
      error: "Access denied",
    }],
  };
  assertEquals(deleteResult.type, "delete");

  // Test InfoResult
  const infoResult: S3Result = {
    type: "info",
    key: "test.txt",
    exists: true,
    size: 1024,
    lastModified: new Date(),
  };
  assertEquals(infoResult.type, "info");

  // Test ErrorResult
  const errorResult: S3Result = {
    type: "error",
    message: "Something went wrong",
    details: { code: "NETWORK_ERROR" },
  };
  assertEquals(errorResult.type, "error");
});