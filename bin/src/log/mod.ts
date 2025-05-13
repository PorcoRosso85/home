/**
 * ログモジュールのエントリポイント
 * -----------------------------------
 * 使用例:
 * 
 * 1. 簡易ロガー（コンソール出力のみ）
 * ```typescript
 * import { debug, info, warn, error } from "./log/mod.ts";
 * 
 * debug("デバッグメッセージ");
 * info("情報メッセージ", { userId: 123 });
 * warn("警告メッセージ");
 * error("エラーメッセージ", new Error("詳細エラー情報"));
 * ```
 * 
 * 2. カスタムロガー（プラグイン組み合わせ）
 * ```typescript
 * import { createLogger, consolePlugin, duckdbPlugin, LogLevel } from "./log/mod.ts";
 * 
 * // コンソール出力 + DuckDB永続化
 * const logger = createLogger([
 *   consolePlugin({ format: 'json', useColors: true }),
 *   duckdbPlugin({ table: 'app_logs', syncMode: 'batch' })
 * ]);
 * 
 * logger.info("アプリ起動");
 * logger.error("接続エラー", { code: "DB_CONN_FAILED" });
 * ```
 * 
 * 3. 既存のSQLリポジトリの直接使用
 * ```typescript
 * import { createSqlClient } from "./log/mod.ts";
 * 
 * const sqlRepo = createSqlClient();
 * await sqlRepo.execute("INSERT INTO logs (code, message) VALUES (?, ?)", ["001", "カスタムログ"]);
 * ```
 * 
 * ログレベル設定:
 * - 環境変数 LOG_LEVEL で設定 (1:ERROR, 2:WARN, 3:INFO, 4:DEBUG)
 * - ブラウザ環境: window.LOG_LEVEL = 4; // DEBUGレベルまで表示
 * - Node環境: process.env.LOG_LEVEL = "3"; // INFOレベルまで表示
 */

// 既存の機能
import { createSqlRepository } from "./infrastructure/duckdb_repository.ts";
import { SqlRepository, Result, SqlError } from "./domain/repository.ts";
import { LogRow } from "./domain/entities.ts";

// 新しいロギングシステム
import { createLogger } from "./infrastructure/logger.ts";
import { consolePlugin } from "./plugins/console.ts";
import { duckdbPlugin } from "./plugins/duckdb.ts";
import { LogLevel, Logger, LoggerOptions, LoggerPlugin, ConsolePluginOptions, DuckDBPluginOptions } from "./domain/type.ts";

// SQLリポジトリのエクスポート (既存機能)
export const createSqlClient = (): SqlRepository => {
  return createSqlRepository();
};

// 便利なデフォルトロガーのエクスポート
export const logger = createLogger([consolePlugin()]);

// ロギング関数の直接エクスポート（簡易使用のため）
export const debug = (message: string, data?: any): void => logger.debug(message, data);
export const info = (message: string, data?: any): void => logger.info(message, data);
export const warn = (message: string, data?: any): void => logger.warn(message, data);
export const error = (message: string, data?: any): void => logger.error(message, data);

// 型定義のエクスポート（既存）
export type { LogRow, SqlRepository, Result, SqlError };

// 新しい型定義と関数のエクスポート
export { 
  createLogger, 
  consolePlugin, 
  duckdbPlugin,
  LogLevel
};

export type {
  Logger,
  LoggerOptions,
  LoggerPlugin,
  ConsolePluginOptions,
  DuckDBPluginOptions
};
