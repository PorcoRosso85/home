/**
 * Execute Query UseCase
 * クエリ実行のビジネスロジック
 */

import type { QueryResult } from "../../domain/types.ts";
import type { DuckDBRepository } from "../../infrastructure/repository/duckdbRepository.ts";

// 依存性の型定義
export type ExecuteQueryDeps = {
  duckdbRepo: DuckDBRepository;
};

// ユースケースの型定義
export type ExecuteQueryUseCase = {
  execute: (query: string) => Promise<QueryResult>;
  executeMultiple: (queries: string[]) => Promise<QueryResult[]>;
  executeWithValidation: (query: string) => Promise<QueryResult>;
};

// クエリの簡易バリデーション
function validateQuery(query: string): QueryResult | null {
  const trimmed = query.trim();
  
  if (!trimmed) {
    return {
      success: false,
      error: "Query cannot be empty",
      code: "VALIDATION_ERROR"
    };
  }
  
  // 危険なクエリのチェック（簡易版）
  const dangerous = ["DROP DATABASE", "DROP SCHEMA", "DETACH DATABASE"];
  const upperQuery = trimmed.toUpperCase();
  
  for (const keyword of dangerous) {
    if (upperQuery.includes(keyword)) {
      return {
        success: false,
        error: `Dangerous operation detected: ${keyword}`,
        code: "VALIDATION_ERROR"
      };
    }
  }
  
  return null;
}

// 高階関数による依存性注入
export function createExecuteQueryUseCase(deps: ExecuteQueryDeps): ExecuteQueryUseCase {
  const { duckdbRepo } = deps;
  
  async function execute(query: string): Promise<QueryResult> {
    return duckdbRepo.executeQuery(query);
  }
  
  async function executeMultiple(queries: string[]): Promise<QueryResult[]> {
    const results: QueryResult[] = [];
    
    for (const query of queries) {
      const result = await execute(query);
      results.push(result);
      
      // エラーが発生したら中断
      if (!result.success) {
        break;
      }
    }
    
    return results;
  }
  
  async function executeWithValidation(query: string): Promise<QueryResult> {
    const validationError = validateQuery(query);
    if (validationError) {
      return validationError;
    }
    
    return execute(query);
  }
  
  return {
    execute,
    executeMultiple,
    executeWithValidation
  };
}

// In-source test
if (!import.meta.main) {
  Deno.test("validateQuery", () => {
    // 空クエリのテスト
    const emptyResult = validateQuery("");
    if (!emptyResult || emptyResult.success !== false) {
      throw new Error("Empty query should return validation error");
    }
    
    // 危険なクエリのテスト
    const dangerousResult = validateQuery("DROP DATABASE test");
    if (!dangerousResult || emptyResult.success !== false) {
      throw new Error("Dangerous query should return validation error");
    }
    
    // 正常なクエリのテスト
    const normalResult = validateQuery("SELECT 1");
    if (normalResult !== null) {
      throw new Error("Normal query should pass validation");
    }
  });
}
