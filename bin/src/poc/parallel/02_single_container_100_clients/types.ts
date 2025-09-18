/**
 * 型定義 - 02 POC用の拡張版
 */

// 01から継承する基本型
export { 
  type HealthResponse,
  type MetricsData,
  type ServerConfig,
} from "../01_single_container_10_clients/types.ts";

// Worker関連の型
export interface WorkerMessage {
  id: string;
  method: string;
  args: unknown[];
}

export interface WorkerResponse {
  id: string;
  result?: unknown;
  error?: string;
}

// キャッシュ関連の型
export interface CacheEntry<T> {
  data: T;
  timestamp: number;
}

// 接続情報の型
export interface Connection {
  id: string;
  conn: Deno.Conn;
  buffer: Uint8Array;
  state: string;
  lastActivity: number;
}

// 拡張サーバー設定
export interface ExtendedServerConfig extends ServerConfig {
  maxConcurrentRequests?: number;
  cacheSize?: number;
  cacheTTL?: number;
  numWorkers?: number;
  customHandler?: (request: Request) => Promise<Response> | Response;
}