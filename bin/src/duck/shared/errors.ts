/**
 * 統合エラー型定義
 * すべての層のエラーを統合し、エラーハンドリングのヘルパー関数を提供
 */

import type { DomainError } from "../domain/errors.ts";
import type { ApplicationError } from "../application/errors.ts";
import type { InfrastructureError } from "../infrastructure/errors.ts";

// すべてのエラーを統合した型
export type AppError = DomainError | ApplicationError | InfrastructureError;

// 成功/失敗の結果型
export type Result<T> = 
  | { success: true; data: T }
  | { success: false; error: AppError };

// エラー判定ヘルパー関数
export function isDomainError(error: AppError): error is DomainError {
  return [
    "INVALID_QUERY",
    "TABLE_NOT_FOUND",
    "PERMISSION_DENIED",
    "INVALID_SYNTAX",
    "CONSTRAINT_VIOLATION"
  ].includes(error.code);
}

export function isApplicationError(error: AppError): error is ApplicationError {
  return [
    "VALIDATION_FAILED",
    "OPERATION_FAILED",
    "DUCKLAKE_NOT_AVAILABLE",
    "CATALOG_CREATION_FAILED",
    "TEST_ENVIRONMENT_FAILED",
    "VERSION_NOT_FOUND"
  ].includes(error.code);
}

export function isInfrastructureError(error: AppError): error is InfrastructureError {
  return [
    "DB_CONNECTION_ERROR",
    "FILE_SYSTEM_ERROR",
    "NETWORK_ERROR",
    "DUCKDB_EXECUTION_ERROR",
    "FILE_NOT_FOUND",
    "PERMISSION_ERROR"
  ].includes(error.code);
}

// エラーコードによるパターンマッチング
export function handleError(error: AppError): string {
  switch (error.code) {
    // Domain errors
    case "INVALID_QUERY":
    case "TABLE_NOT_FOUND":
    case "PERMISSION_DENIED":
    case "INVALID_SYNTAX":
    case "CONSTRAINT_VIOLATION":
      return `Domain Error [${error.code}]: ${error.message}`;
    
    // Application errors
    case "VALIDATION_FAILED":
    case "OPERATION_FAILED":
    case "DUCKLAKE_NOT_AVAILABLE":
    case "CATALOG_CREATION_FAILED":
    case "TEST_ENVIRONMENT_FAILED":
      return `Application Error [${error.code}]: ${error.message}`;
    
    // Infrastructure errors
    case "DB_CONNECTION_ERROR":
    case "FILE_SYSTEM_ERROR":
    case "NETWORK_ERROR":
    case "DUCKDB_EXECUTION_ERROR":
    case "FILE_NOT_FOUND":
    case "PERMISSION_ERROR":
      return `Infrastructure Error [${error.code}]: ${error.message}`;
    
    default:
      // 網羅性チェック（TypeScriptでnever型になる）
      const _exhaustive: never = error;
      return `Unknown error: ${JSON.stringify(error)}`;
  }
}

// HTTPステータスコードへのマッピング
export function getHttpStatusCode(error: AppError): number {
  switch (error.code) {
    // 400 Bad Request
    case "INVALID_QUERY":
    case "VALIDATION_FAILED":
    case "INVALID_SYNTAX":
      return 400;
    
    // 404 Not Found
    case "TABLE_NOT_FOUND":
    case "FILE_NOT_FOUND":
      return 404;
    
    // 403 Forbidden
    case "PERMISSION_DENIED":
    case "PERMISSION_ERROR":
      return 403;
    
    // 503 Service Unavailable
    case "DUCKLAKE_NOT_AVAILABLE":
    case "DB_CONNECTION_ERROR":
      return 503;
    
    // 500 Internal Server Error
    default:
      return 500;
  }
}

// テスト用のエラー生成ヘルパー
export function createTestError(type: "domain" | "application" | "infrastructure"): AppError {
  switch (type) {
    case "domain":
      return { code: "INVALID_QUERY", message: "Test domain error" };
    case "application":
      return { code: "VALIDATION_FAILED", message: "Test application error", details: {} };
    case "infrastructure":
      return { code: "DB_CONNECTION_ERROR", message: "Test infrastructure error" };
  }
}
