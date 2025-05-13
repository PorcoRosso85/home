/**
 * DuckDB永続化プラグイン
 * SQLを使ったログの永続化機能を提供
 */
import { DuckDBPluginOptions, LogLevel, LoggerPlugin } from "../domain/type.ts";
import { createSqlRepository } from "../infrastructure/duckdb_repository.ts";
import { LogRow } from "../domain/entities.ts";

// デフォルトオプション
const DEFAULT_OPTIONS: DuckDBPluginOptions = {
  table: 'logs',
  batchSize: 10,
  syncMode: 'immediate',
  intervalMs: 5000
};

// ログレベルを文字列に変換
const logLevelToString = (level: LogLevel): string => {
  switch (level) {
    case LogLevel.ERROR: return 'ERROR';
    case LogLevel.WARN: return 'WARN';
    case LogLevel.INFO: return 'INFO';
    case LogLevel.DEBUG: return 'DEBUG';
    default: return 'UNKNOWN';
  }
};

// プラグイン実装
export const duckdbPlugin = (options?: Partial<DuckDBPluginOptions>): LoggerPlugin => {
  // オプションの設定（デフォルトとマージ）
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  // SQLリポジトリの取得
  const repository = createSqlRepository();
  
  // バッチ処理用のキュー
  let queue: LogRow[] = [];
  let timer: number | undefined;
  
  // テーブル作成を確保
  const ensureTable = async (): Promise<void> => {
    const result = await repository.execute(`
      CREATE TABLE IF NOT EXISTS ${opts.table} (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT,
        level TEXT,
        code TEXT,
        message TEXT,
        error TEXT,
        metadata TEXT
      )
    `);
    
    if (!result.ok) {
      console.error(`Failed to create logs table: ${result.error.message}`);
    }
  };
  
  // キューに溜まったログをDBに書き込む
  const flushQueue = async (): Promise<void> => {
    if (queue.length === 0) return;
    
    const batchToProcess = [...queue];
    queue = [];
    
    for (const log of batchToProcess) {
      const values = [
        log.timestamp || new Date().toISOString(),
        log.level || 'UNKNOWN',
        log.code,
        log.message || '',
        JSON.stringify(log.error),
        log.metadata ? JSON.stringify(log.metadata) : null
      ];
      
      const result = await repository.execute(
        `INSERT INTO ${opts.table} (timestamp, level, code, message, error, metadata)
         VALUES (?, ?, ?, ?, ?, ?)`,
        values
      );
      
      if (!result.ok) {
        console.error(`Failed to insert log: ${result.error.message}`, log);
      }
    }
  };
  
  // プラグイン初期化
  ensureTable().catch(err => {
    console.error('Failed to initialize duckdb plugin:', err);
  });
  
  // インターバルモードの場合、定期的にフラッシュするタイマーを設定
  if (opts.syncMode === 'interval' && opts.intervalMs) {
    timer = setInterval(flushQueue, opts.intervalMs) as unknown as number;
  }
  
  return {
    name: 'duckdb',
    process: async (level: LogLevel, message: string, data?: any): Promise<void> => {
      const logEntry: LogRow = {
        timestamp: new Date().toISOString(),
        level: logLevelToString(level),
        code: '000', // デフォルトコード
        message,
        error: data instanceof Error 
          ? { 
              message: data.message,
              stack: data.stack,
              name: data.name
            } 
          : (data || {}),
        metadata: { timestamp: Date.now() }
      };
      
      // ログエントリをキューに追加
      queue.push(logEntry);
      
      // 同期モードに基づいて処理
      if (opts.syncMode === 'immediate') {
        await flushQueue();
      } else if (opts.syncMode === 'batch' && queue.length >= (opts.batchSize || 10)) {
        await flushQueue();
      }
      // intervalモードの場合は、タイマーに任せる
    }
  };
};
