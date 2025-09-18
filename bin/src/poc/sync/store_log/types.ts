// 型定義、データ構造

// CausalOperationの再エクスポート（依存を明確化）
import type { CausalOperation } from "./causal-sync-client.ts";
export type { CausalOperation };

export interface EventLogConfig {
  readonly path: string;
  readonly format: 'jsonl';
  readonly syncWrites?: boolean;
}

export interface EventLogReader {
  readEvents(fromOffset?: number): Promise<CausalOperation[]>;
  getLatestOffset(): Promise<number>;
  stream(): ReadableStream<CausalOperation>;
}

export interface EventLogWriter {
  append(event: CausalOperation): Promise<number>;
}

export interface EventLogPersistence extends EventLogReader, EventLogWriter {
  close(): Promise<void>;
}