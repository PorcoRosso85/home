import { LogRow } from "./entities.ts";

// エラー型の定義
export type SqlError = {
  message: string;
  code: string;
  cause?: unknown;
};

// 関数の結果型（成功またはエラー）
export type Result<T> = 
  | { ok: true; value: T }
  | { ok: false; error: SqlError };

// 最小限のSQLリポジトリ
export type SqlRepository = {
  execute: (sql: string, params?: unknown[]) => Promise<Result<LogRow[]>>;
};
