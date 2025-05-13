import { createSqlRepository } from "./infrastructure/duckdb_repository.ts";
import { SqlRepository, Result, SqlError } from "./domain/repository.ts";
import { LogRow } from "./domain/entities.ts";

// SQLリポジトリのエクスポート
export const createSqlClient = (): SqlRepository => {
  return createSqlRepository();
};

// 型定義のエクスポート
export type { LogRow, SqlRepository, Result, SqlError };
