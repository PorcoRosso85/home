// 型定義とデータ構造
// bin/docs規約準拠: エラーを戻り値として扱う

export type ServerConfig = {
  name: string;
  port: number;
  partitionKey: string;
  peerServer: string;
  database: DatabaseConfig;
};

export type DatabaseConfig = {
  hostname: string;
  port: number;
  database: string;
  user: string;
  password: string;
};

// エラーを戻り値として扱う（規約準拠）
export type ServerResult<T> = 
  | { ok: true; data: T }
  | { ok: false; error: ServerError };

export type ServerError = {
  code: string;
  message: string;
  server?: string;
  details?: unknown;
};

export type UserProfile = {
  userId: string;
  server: string;
  partition: string;
  createdAt?: Date;
};

export type GlobalSetting = {
  key: string;
  value: unknown;
  updatedAt: Date;
  synced?: boolean;
};

export type SyncOperation = {
  path: string;
  data: string;
  createdAt: Date;
  processed?: boolean;
};

export type HealthStatus = {
  status: 'healthy' | 'unhealthy';
  server: string;
  database: 'connected' | 'disconnected';
  peer: 'healthy' | 'unreachable' | 'unknown';
  uptime: number;
};

export type MetricsData = {
  server: string;
  partition: string;
  totalUsers: number;
  totalSettings: number;
  pendingSyncs: number;
  connections: {
    active: number;
    idle: number;
    waiting: number;
  };
};