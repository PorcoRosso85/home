/**
 * 統合エラー型定義
 * すべての層のエラーを統合し、エラーハンドリングのヘルパー関数を提供
 */

import type { DomainError } from "../domain/errors.ts";
import type { ApplicationError } from "../application/errors.ts";
import type { InfrastructureError } from "../infrastructure/errors.ts";

// すべてのエラーを統合した型
export type AppError = DomainError | ApplicationError | InfrastructureError;

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

// エラーチェックヘルパー（共用体型での判定用）
export function isError(value: any): value is AppError {
  return value && typeof value === 'object' && 'code' in value && 'message' in value;
}

// エラーフォーマッティング（プレフィックス追加のみ、元のメッセージは完全保持）
export type FormattedError = {
  code: string;
  message: string;
  originalMessage: string;
  details?: any;
  filePath?: string;
  operation?: string;
  query?: string;
  version?: string;
};

export function formatError(error: AppError): FormattedError {
  // エラータイプに基づくプレフィックスを決定
  let prefix = "";
  
  if (isDomainError(error)) {
    prefix = "[Domain Error]";
  } else if (isApplicationError(error)) {
    prefix = "[Application Error]";
  } else if (isInfrastructureError(error)) {
    prefix = "[Infrastructure Error]";
  } else {
    prefix = "[Unknown Error]";
  }
  
  // プレフィックスを追加し、元のメッセージは完全保持
  const { code, message, ...rest } = error;
  
  return {
    code,
    message: `${prefix} ${message}`,
    originalMessage: message,
    ...rest // その他の追加プロパティを保持
  };
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
    case "VERSION_NOT_FOUND":
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