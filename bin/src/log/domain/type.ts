/**
 * ログシステムの基本型定義
 */

// ログレベル定義
export const enum LogLevel {
  ERROR = 1,
  WARN = 2,
  INFO = 3,
  DEBUG = 4
}

// ログレベル文字列表現
export type LogLevelString = 'error' | 'warn' | 'info' | 'debug';

// コンソールプラグイン用のフォーマット定義
export type ConsoleFormat = 'simple' | 'json' | 'detailed';

// コンソールプラグインのオプション型
export type ConsolePluginOptions = {
  format?: ConsoleFormat;
  useColors?: boolean;
  timestampFormat?: 'iso' | 'local' | 'relative';
};

// DuckDBプラグインのオプション型
export type DuckDBPluginOptions = {
  table?: string;
  batchSize?: number;
  syncMode?: 'immediate' | 'batch' | 'interval';
  intervalMs?: number;
};

// ロガーのメッセージ処理関数型
export type LogProcessFunction = (level: LogLevel, message: string, data?: any) => void;

// ロガープラグイン型
export type LoggerPlugin = {
  name: string;
  process: LogProcessFunction;
};

// ロガーの基本インスタンス型
export type Logger = {
  log: (level: LogLevel, message: string, data?: any) => void;
  error: (message: string, data?: any) => void;
  warn: (message: string, data?: any) => void;
  info: (message: string, data?: any) => void;
  debug: (message: string, data?: any) => void;
};

// ロガーオプション型
export type LoggerOptions = {
  level?: LogLevel;
  defaultPluginOptions?: Record<string, unknown>;
};
