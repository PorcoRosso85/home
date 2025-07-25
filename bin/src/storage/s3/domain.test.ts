/**
 * Tests for domain types and logic
 */

import { assertEquals, assertThrows } from "https://deno.land/std@0.208.0/assert/mod.ts";
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
import { validateS3Key, validateS3ObjectSize, validateS3BucketName } from "./domain.ts";

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

// S3 Object Key Validation Tests (RED Phase)
Deno.test("S3 key validation: should reject keys exceeding maximum length to prevent storage errors", () => {
  // AWS S3 keys have a maximum length of 1024 bytes (not characters)
  // This prevents storage system errors and ensures compatibility
  const tooLongKey = "a".repeat(1025);
  
  assertThrows(
    () => validateS3Key(tooLongKey),
    Error,
    "S3 key exceeds maximum length of 1024 bytes"
  );
});

Deno.test("S3 key validation: should reject keys with null bytes to prevent security vulnerabilities", () => {
  // Null bytes can cause path traversal attacks and break file system operations
  // This protects against injection attacks and ensures safe storage
  const keyWithNullByte = "file\x00.txt";
  
  assertThrows(
    () => validateS3Key(keyWithNullByte),
    Error,
    "S3 key contains invalid characters"
  );
});

Deno.test("S3 key validation: should reject keys with control characters to ensure data integrity", () => {
  // Control characters can corrupt data streams and cause parsing errors
  // This ensures reliable data retrieval and prevents data corruption
  const keyWithControlChar = "file\x01\x02.txt";
  
  assertThrows(
    () => validateS3Key(keyWithControlChar),
    Error,
    "S3 key contains invalid characters"
  );
});

Deno.test("S3 key validation: should accept valid keys to enable normal operations", () => {
  // Valid keys allow proper storage and retrieval of objects
  // This ensures the system works correctly for legitimate use cases
  const validKeys = [
    "documents/report.pdf",
    "images/photo-2024.jpg",
    "data/users/123/profile.json",
    "backups/2024-01-01/database.sql.gz",
    "a".repeat(1024), // Maximum valid length
  ];
  
  for (const key of validKeys) {
    // Should not throw
    validateS3Key(key);
  }
});

// S3 Object Size Validation Tests (RED Phase)
Deno.test("S3 object size validation: should reject objects exceeding 5GB limit to prevent upload failures", () => {
  // AWS S3 has a maximum object size of 5GB for single PUT operations
  // This prevents failed uploads and ensures compatibility with S3 limits
  const maxSize = 5 * 1024 * 1024 * 1024; // 5GB in bytes
  const oversizedObject = maxSize + 1; // 1 byte over the limit
  
  assertThrows(
    () => validateS3ObjectSize(oversizedObject),
    Error,
    "Object size exceeds S3 limit of 5GB"
  );
});

Deno.test("S3 object size validation: should reject negative sizes to prevent data corruption", () => {
  // Negative sizes are invalid and indicate corrupted data or programming errors
  // This protects against invalid state and ensures data integrity
  const negativeSize = -1;
  
  assertThrows(
    () => validateS3ObjectSize(negativeSize),
    Error,
    "Object size must be non-negative"
  );
});

Deno.test("S3 object size validation: should accept objects at exactly 5GB limit to maximize storage efficiency", () => {
  // Objects exactly at the 5GB limit should be allowed
  // This ensures we can use the full capacity allowed by S3
  const maxSize = 5 * 1024 * 1024 * 1024; // Exactly 5GB in bytes
  
  // Should not throw
  validateS3ObjectSize(maxSize);
});

Deno.test("S3 object size validation: should accept common file sizes to enable normal operations", () => {
  // Common file sizes should be accepted for normal operations
  // This ensures the system works correctly for typical use cases
  const validSizes = [
    0, // Empty file
    1024, // 1KB
    1024 * 1024, // 1MB
    100 * 1024 * 1024, // 100MB
    1024 * 1024 * 1024, // 1GB
    4 * 1024 * 1024 * 1024, // 4GB
  ];
  
  for (const size of validSizes) {
    // Should not throw
    validateS3ObjectSize(size);
  }
});

// S3 Bucket Name Validation Tests (RED Phase)
Deno.test("S3 bucket name validation: should reject names shorter than 3 characters to meet AWS requirements", () => {
  // AWS requires bucket names to be at least 3 characters for uniqueness
  // This prevents namespace conflicts and ensures global uniqueness
  const tooShortNames = ["", "a", "ab"];
  
  for (const name of tooShortNames) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name must be between 3 and 63 characters"
    );
  }
});

Deno.test("S3 bucket name validation: should reject names longer than 63 characters to comply with DNS limitations", () => {
  // S3 bucket names are mapped to DNS subdomains which have a 63 character limit
  // This ensures bucket names can be used in virtual-hosted-style URLs
  const tooLongName = "a".repeat(64);
  
  assertThrows(
    () => validateS3BucketName(tooLongName),
    Error,
    "Bucket name must be between 3 and 63 characters"
  );
});

Deno.test("S3 bucket name validation: should reject uppercase letters to ensure DNS compatibility", () => {
  // DNS names are case-insensitive but S3 enforces lowercase for consistency
  // This prevents access issues and ensures uniform naming across regions
  const namesWithUppercase = [
    "MyBucket",
    "BUCKET",
    "test-Bucket-123",
    "camelCaseBucket",
  ];
  
  for (const name of namesWithUppercase) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name must contain only lowercase letters, numbers, and hyphens"
    );
  }
});

Deno.test("S3 bucket name validation: should reject special characters to prevent URL encoding issues", () => {
  // Special characters can cause problems in URLs and APIs
  // This ensures buckets are accessible through all S3 interfaces
  const namesWithSpecialChars = [
    "my_bucket", // underscore
    "my.bucket", // period (not allowed in bucket names)
    "my bucket", // space
    "my@bucket", // at symbol
    "my#bucket", // hash
    "my$bucket", // dollar sign
    "my%bucket", // percent
    "my&bucket", // ampersand
    "my*bucket", // asterisk
    "my+bucket", // plus
    "my=bucket", // equals
    "my!bucket", // exclamation
    "my?bucket", // question mark
    "my/bucket", // forward slash
    "my\\bucket", // backslash
  ];
  
  for (const name of namesWithSpecialChars) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name must contain only lowercase letters, numbers, and hyphens"
    );
  }
});

Deno.test("S3 bucket name validation: should reject consecutive hyphens to avoid DNS parsing ambiguity", () => {
  // Consecutive hyphens can be misinterpreted in DNS and URLs
  // This ensures bucket names are unambiguous in all contexts
  const namesWithConsecutiveHyphens = [
    "my--bucket",
    "test---bucket",
    "bucket--name--123",
  ];
  
  for (const name of namesWithConsecutiveHyphens) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name cannot contain consecutive hyphens"
    );
  }
});

Deno.test("S3 bucket name validation: should reject names starting with hyphen to comply with DNS label rules", () => {
  // DNS labels cannot start with a hyphen per RFC 952
  // This ensures bucket names are valid DNS subdomains
  const namesStartingWithHyphen = [
    "-bucket",
    "-my-bucket",
    "-123-bucket",
  ];
  
  for (const name of namesStartingWithHyphen) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name must start and end with a letter or number"
    );
  }
});

Deno.test("S3 bucket name validation: should reject names ending with hyphen to comply with DNS label rules", () => {
  // DNS labels cannot end with a hyphen per RFC 952
  // This ensures bucket names are valid DNS subdomains
  const namesEndingWithHyphen = [
    "bucket-",
    "my-bucket-",
    "bucket-123-",
  ];
  
  for (const name of namesEndingWithHyphen) {
    assertThrows(
      () => validateS3BucketName(name),
      Error,
      "Bucket name must start and end with a letter or number"
    );
  }
});

Deno.test("S3 bucket name validation: should accept valid bucket names to enable normal S3 operations", () => {
  // Valid bucket names allow creation and access of S3 buckets
  // This ensures the system works correctly for legitimate use cases
  const validBucketNames = [
    "abc", // minimum length
    "my-bucket",
    "test-bucket-123",
    "data-storage-2024",
    "backup-us-east-1",
    "123-numeric-start",
    "numeric-end-456",
    "a".repeat(63), // maximum length
    "multi-part-bucket-name-with-numbers-123",
  ];
  
  for (const name of validBucketNames) {
    // Should not throw
    validateS3BucketName(name);
  }
});