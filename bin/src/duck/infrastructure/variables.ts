/**
 * Infrastructure Variables Configuration
 * 環境変数と内部定数を集約
 */

// ========== 環境変数 ==========
/**
 * ログレベル設定
 * 0: OFF, 1: ERROR, 2: WARN, 3: INFO, 4: DEBUG
 */
export const LOG_LEVEL = parseInt(Deno.env.get("LOG_LEVEL") || "3", 10);

/**
 * サーバーポート
 */
export const PORT = parseInt(Deno.env.get("PORT") || "8000", 10);

/**
 * データファイルパス
 * テスト時は動的に設定される
 */
export const DATA_FILES_PATH = Deno.env.get("DATA_FILES_PATH") || "./data_files";

/**
 * DuckDBデータベースパス
 * テスト時は動的に設定される
 */
export const DUCKLAKE_DB_PATH = Deno.env.get("DUCKLAKE_DB_PATH") || "ducklake.db";

// ========== 内部定数 ==========
/**
 * サーバー名
 */
export const SERVER_NAME = "DuckDB Server with DuckLake (v1.3.0+)" as const;

/**
 * APIレスポンスのContent-Type
 */
export const CONTENT_TYPE_JSON = "application/json" as const;

/**
 * ファイル名のプレフィックス
 */
export const FILE_PREFIX = "ducklake-" as const;

/**
 * ファイルタイプ
 */
export const FILE_TYPES = {
  DATA: "data",
  SNAPSHOT: "snapshot",
} as const;

/**
 * APIエンドポイント
 */
export const ENDPOINTS = {
  ROOT: "/",
  QUERY: "/query",
} as const;

/**
 * ディレクトリ構造
 */
export const DIRECTORIES = {
  DATA_SUBDIR: "data",
  SNAPSHOT_SUBDIR: "snapshots",
} as const;

/**
 * テスト設定
 */
export const TEST_CONFIG = {
  /** テスト用一時ディレクトリのプレフィックス */
  TEMP_DIR_PREFIX: "ducklake_test",
  /** テストタイムアウト（ミリ秒） */
  TIMEOUT_MS: 30000,
} as const;

/**
 * DuckDB設定
 */
export const DUCKDB_CONFIG = {
  /** 最大メモリ使用量 */
  MAX_MEMORY: "512MB",
  /** スレッド数 */
  THREADS: 4,
} as const;

/**
 * テスト用ヘルパー関数
 * テスト環境用の変数を設定
 */
export function setTestDataPath(path: string): void {
  Deno.env.set("DATA_FILES_PATH", path);
}

/**
 * 現在のデータファイルパスを取得
 */
export function getCurrentDataPath(): string {
  return Deno.env.get("DATA_FILES_PATH") || DATA_FILES_PATH;
}
