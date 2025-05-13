/**
 * コンソール出力プラグイン
 * コンソールへのログ出力機能を提供
 */
import { ConsolePluginOptions, LogLevel, LoggerPlugin } from "../domain/type.ts";

// デフォルトオプション
const DEFAULT_OPTIONS: ConsolePluginOptions = {
  format: 'simple',
  useColors: true,
  timestampFormat: 'iso'
};

// カラーコード（ターミナルでの色表示用）
const COLORS = {
  reset: "\x1b[0m",
  red: "\x1b[31m",
  yellow: "\x1b[33m",
  blue: "\x1b[34m",
  gray: "\x1b[90m"
};

// タイムスタンプをフォーマットする関数
const formatTimestamp = (format: 'iso' | 'local' | 'relative'): string => {
  const now = new Date();
  switch (format) {
    case 'iso':
      return `[${now.toISOString()}]`;
    case 'local':
      return `[${now.toLocaleString()}]`;
    case 'relative':
      return `[+${Date.now() - performance.now()}ms]`;
    default:
      return `[${now.toISOString()}]`;
  }
};

// ログレベルに応じたラベルとカラーを取得
const getLevelInfo = (level: LogLevel, useColors: boolean) => {
  switch (level) {
    case LogLevel.ERROR:
      return { 
        label: 'ERROR', 
        color: useColors ? COLORS.red : '', 
        method: console.error 
      };
    case LogLevel.WARN:
      return { 
        label: 'WARN', 
        color: useColors ? COLORS.yellow : '', 
        method: console.warn 
      };
    case LogLevel.INFO:
      return { 
        label: 'INFO', 
        color: useColors ? COLORS.blue : '', 
        method: console.info 
      };
    case LogLevel.DEBUG:
      return { 
        label: 'DEBUG', 
        color: useColors ? COLORS.gray : '', 
        method: console.debug 
      };
    default:
      return { 
        label: 'LOG', 
        color: '', 
        method: console.log 
      };
  }
};

// プラグイン実装
export const consolePlugin = (options?: Partial<ConsolePluginOptions>): LoggerPlugin => {
  // オプションの設定（デフォルトとマージ）
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  return {
    name: 'console',
    process: (level: LogLevel, message: string, data?: any): void => {
      const timestamp = formatTimestamp(opts.timestampFormat || 'iso');
      const { label, color, method } = getLevelInfo(level, opts.useColors || false);
      
      // フォーマットに基づいてログメッセージ生成
      switch (opts.format) {
        case 'json':
          method(JSON.stringify({
            timestamp: new Date().toISOString(),
            level: label,
            message,
            data
          }));
          break;
          
        case 'detailed':
          if (opts.useColors) {
            method(
              `${timestamp} ${color}[${label}]${COLORS.reset} ${message}`,
              data !== undefined ? data : ''
            );
          } else {
            method(
              `${timestamp} [${label}] ${message}`,
              data !== undefined ? data : ''
            );
          }
          break;
          
        case 'simple':
        default:
          if (opts.useColors) {
            method(
              `${color}${message}${COLORS.reset}`,
              data !== undefined ? data : ''
            );
          } else {
            method(message, data !== undefined ? data : '');
          }
          break;
      }
    }
  };
};
