// 公開APIのエクスポート
// bin/docs規約準拠: mod.tsから一元エクスポート

// 型定義
export type {
  ServerConfig,
  DatabaseConfig,
  ServerResult,
  ServerError,
  UserProfile,
  GlobalSetting,
  SyncOperation,
  HealthStatus,
  MetricsData
} from "./types/server.ts";

// コアビジネスロジック（純粋関数）
export {
  isInPartition,
  getCorrectServer,
  isValidPartitionKey,
  areComplementaryPartitions
} from "./core/partition.ts";

// アダプター
export { DatabaseAdapter } from "./adapters/database.ts";
export { HttpClient } from "./adapters/http-client.ts";
export type { HttpResponse } from "./adapters/http-client.ts";

// サーバー実装
export { DualServerApplication } from "./server.ts";