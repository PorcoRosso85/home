/**
 * 環境変数とグローバル設定
 * 
 * 規約準拠:
 * - module_design.md: 環境変数の一元管理
 * - error_handling.md: 設定エラーの適切な処理
 */

import { homedir } from "node:os";
import { join } from "node:path";

/**
 * KuzuDBのパスを環境変数から取得
 * @returns パス文字列
 */
export function getKuzuPath(): string {
  const path = Deno.env.get("KUZU_DB_PATH");
  if (!path) {
    // デフォルトパスを使用
    return join(homedir(), ".kuzu", "default.db");
  }
  return path;
}

/**
 * クエリキャッシュが有効かどうかを環境変数から取得
 * @returns キャッシュ有効フラグ（デフォルト: true）
 */
export function getCacheEnabled(): boolean {
  const cacheEnabled = Deno.env.get("KUZU_TS_CACHE_ENABLED") ?? "true";
  return ["true", "1", "yes", "on"].includes(cacheEnabled.toLowerCase());
}

/**
 * クエリキャッシュの最大サイズを取得
 * @returns 最大キャッシュサイズ（デフォルト: 100）
 */
export function getMaxCacheSize(): number {
  const maxCacheSize = Deno.env.get("KUZU_TS_MAX_CACHE_SIZE");
  if (maxCacheSize) {
    const parsed = parseInt(maxCacheSize, 10);
    if (!isNaN(parsed)) {
      return parsed;
    }
  }
  return 100;
}

/**
 * デバッグモードが有効かどうかを取得
 * @returns デバッグモードフラグ（デフォルト: false）
 */
export function getDebugMode(): boolean {
  const debug = Deno.env.get("KUZU_TS_DEBUG") ?? "false";
  return ["true", "1", "yes", "on"].includes(debug.toLowerCase());
}

// グローバル定数
/** デフォルトのデータベース最大サイズ (1GB) */
export const DEFAULT_DB_MAX_SIZE = 1 << 30;  // 1GB

/** デフォルトのキャッシュTTL（1時間、秒単位） */
export const DEFAULT_CACHE_TTL = 3600;

/** サポートされるクエリタイプ */
export const VALID_QUERY_TYPES = ["dml", "dql", "auto"] as const;
export type QueryType = typeof VALID_QUERY_TYPES[number];

/** クエリファイルの拡張子 */
export const QUERY_FILE_EXTENSION = ".cypher";

/** デフォルトクエリディレクトリ */
export const DEFAULT_QUERY_DIR = "./queries";

// 将来の拡張のための設定インターフェース
export interface KuzuConfig {
  dbPath?: string;
  maxDbSize?: number;
  cacheEnabled?: boolean;
  maxCacheSize?: number;
  debugMode?: boolean;
  cacheTTL?: number;
}

/**
 * デフォルト設定を取得
 * @returns デフォルトのKuzu設定
 */
export function getDefaultConfig(): KuzuConfig {
  return {
    dbPath: getKuzuPath(),
    maxDbSize: DEFAULT_DB_MAX_SIZE,
    cacheEnabled: getCacheEnabled(),
    maxCacheSize: getMaxCacheSize(),
    debugMode: getDebugMode(),
    cacheTTL: DEFAULT_CACHE_TTL,
  };
}

/**
 * 環境変数と提供された設定をマージ
 * @param config 部分的な設定オブジェクト
 * @returns マージされた設定
 */
export function mergeConfig(config?: Partial<KuzuConfig>): KuzuConfig {
  const defaultConfig = getDefaultConfig();
  return {
    ...defaultConfig,
    ...config,
  };
}