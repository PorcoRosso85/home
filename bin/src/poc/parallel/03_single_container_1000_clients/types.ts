/**
 * 型定義 - 03 極限最適化版
 */

// 基本型定義（02から継承した知識を独立実装）
export interface HealthResponse {
  status: string;
  timestamp: string;
  uptime: number;
}

export interface MetricsData {
  requestCount: number;
  errorCount: number;
  responseTimes: number[];
  memory: {
    rss: number;
    heapTotal: number;
    heapUsed: number;
    external: number;
  };
}

export interface Connection {
  id: string;
  conn: Deno.Conn;
  buffer: Uint8Array;
  state: string;
  lastActivity: number;
}

export interface ServerConfig {
  port: number;
  maxMetricsSize: number;
}

export interface ExtendedServerConfig extends ServerConfig {
  maxConcurrentRequests?: number;
  cacheSize?: number;
  cacheTTL?: number;
  numWorkers?: number;
}

// バッファプール用の型
export interface PooledBuffer {
  buffer: Uint8Array;
  inUse: boolean;
  lastUsed: number;
}

// 極限最適化設定
export interface ExtremeServerConfig extends ExtendedServerConfig {
  tcpNoDelay?: boolean;
  tcpKeepAlive?: boolean;
  tcpKeepAliveInitialDelay?: number;
  maxConnectionsPerIP?: number;
  connectionTimeout?: number;
  requestQueueSize?: number;
  enableZeroCopy?: boolean;
  preallocateBuffers?: number;
}

// パフォーマンスカウンター
export interface PerformanceCounters {
  totalConnections: number;
  activeConnections: number;
  rejectedConnections: number;
  totalRequests: number;
  queuedRequests: number;
  droppedRequests: number;
  avgProcessingTime: number;
  gcCount: number;
  lastGcTime: number;
}