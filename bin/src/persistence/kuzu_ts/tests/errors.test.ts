import { assertEquals, assertStrictEquals } from "https://deno.land/std@0.224.0/assert/mod.ts";
import {
  createFileOperationError,
  createValidationError,
  createNotFoundError,
  isFileOperationError,
  isValidationError,
  isNotFoundError,
  isKuzuError,
  type FileOperationError,
  type ValidationError,
  type NotFoundError,
} from "../mod.ts";

Deno.test("FileOperationError creation and type guard", () => {
  const error = createFileOperationError(
    "Failed to read file",
    "read",
    "/path/to/file",
    {
      permission_issue: true,
      exists: false,
    }
  );

  assertEquals(error.type, "FileOperationError");
  assertEquals(error.message, "Failed to read file");
  assertEquals(error.operation, "read");
  assertEquals(error.file_path, "/path/to/file");
  assertEquals(error.permission_issue, true);
  assertEquals(error.exists, false);

  assertStrictEquals(isFileOperationError(error), true);
  assertStrictEquals(isValidationError(error), false);
  assertStrictEquals(isNotFoundError(error), false);
  assertStrictEquals(isKuzuError(error), true);
});

Deno.test("ValidationError creation and type guard", () => {
  const error = createValidationError(
    "Invalid value",
    "email",
    "not-an-email",
    "email format",
    "Use format: user@example.com"
  );

  assertEquals(error.type, "ValidationError");
  assertEquals(error.message, "Invalid value");
  assertEquals(error.field, "email");
  assertEquals(error.value, "not-an-email");
  assertEquals(error.constraint, "email format");
  assertEquals(error.suggestion, "Use format: user@example.com");

  assertStrictEquals(isValidationError(error), true);
  assertStrictEquals(isFileOperationError(error), false);
  assertStrictEquals(isNotFoundError(error), false);
  assertStrictEquals(isKuzuError(error), true);
});

Deno.test("NotFoundError creation and type guard", () => {
  const error = createNotFoundError(
    "Resource not found",
    "User",
    "123",
    ["/users", "/api/users"]
  );

  assertEquals(error.type, "NotFoundError");
  assertEquals(error.message, "Resource not found");
  assertEquals(error.resource_type, "User");
  assertEquals(error.resource_id, "123");
  assertEquals(error.search_locations, ["/users", "/api/users"]);

  assertStrictEquals(isNotFoundError(error), true);
  assertStrictEquals(isFileOperationError(error), false);
  assertStrictEquals(isValidationError(error), false);
  assertStrictEquals(isKuzuError(error), true);
});

Deno.test("Type guards handle non-error objects", () => {
  assertStrictEquals(isFileOperationError(null), false);
  assertStrictEquals(isFileOperationError(undefined), false);
  assertStrictEquals(isFileOperationError({}), false);
  assertStrictEquals(isFileOperationError({ type: "wrong" }), false);
  assertStrictEquals(isFileOperationError("string"), false);
  assertStrictEquals(isFileOperationError(123), false);

  assertStrictEquals(isKuzuError(null), false);
  assertStrictEquals(isKuzuError(undefined), false);
  assertStrictEquals(isKuzuError({}), false);
});

Deno.test("Optional fields work correctly", () => {
  const fileError = createFileOperationError(
    "Operation failed",
    "write",
    "/path/to/file"
  );

  assertEquals(fileError.permission_issue, undefined);
  assertEquals(fileError.exists, undefined);

  const validationError = createValidationError(
    "Invalid input",
    "age",
    "-5",
    "positive number"
  );

  assertEquals(validationError.suggestion, undefined);

  const notFoundError = createNotFoundError(
    "Not found",
    "Article",
    "abc"
  );

  assertEquals(notFoundError.search_locations, undefined);
});