/**
 * 型定義 - エラー処理のための戻り値型
 */
import type { Database, Connection } from "kuzu";
import type { FileOperationError, ValidationError } from "./errors.ts";

// Result型の定義（規約に従い、ジェネリックResultは使わない）
export type DatabaseResult = Database | FileOperationError | ValidationError;
export type ConnectionResult = Connection | FileOperationError | ValidationError;

// Type guard functions
export function isDatabase(result: DatabaseResult): result is Database {
  return (
    typeof result === "object" &&
    result !== null &&
    !("type" in result) &&
    "close" in result &&
    !("execute" in result)  // Database has close but not execute
  );
}

export function isConnection(result: ConnectionResult): result is Connection {
  return (
    typeof result === "object" &&
    result !== null &&
    !("type" in result) &&
    "query" in result &&
    "execute" in result
  );
}

export function isFileOperationError(
  result: DatabaseResult | ConnectionResult
): result is FileOperationError {
  return (
    typeof result === "object" &&
    result !== null &&
    "type" in result &&
    result.type === "FileOperationError"
  );
}

export function isValidationError(
  result: DatabaseResult | ConnectionResult
): result is ValidationError {
  return (
    typeof result === "object" &&
    result !== null &&
    "type" in result &&
    result.type === "ValidationError"
  );
}