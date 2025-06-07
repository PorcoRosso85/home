/**
 * Deno環境用のロガー実装
 * Kuzuからの移植版
 */
import { LogLevel, LOG_LEVEL } from './variables.ts';

// 色定義（ANSI escape codes）
const Colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  red: '\x1b[31m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  gray: '\x1b[90m',
  cyan: '\x1b[36m'
} as const;

// タイムスタンプを取得する関数
const getTimestamp = () => {
  const now = new Date();
  return now.toISOString();
};

// ログレベルごとの色を取得
const getLevelColor = (level: string): string => {
  switch (level) {
    case 'ERROR': return Colors.red;
    case 'WARN': return Colors.yellow;
    case 'INFO': return Colors.cyan;
    case 'DEBUG': return Colors.gray;
    default: return Colors.reset;
  }
};

// フォーマット済みメッセージを作成
const formatMessage = (level: string, message: string, data?: any): string => {
  const timestamp = getTimestamp();
  const color = getLevelColor(level);
  const prefix = `${Colors.gray}[${timestamp}]${Colors.reset} ${color}[${level}]${Colors.reset}`;
  
  let fullMessage = `${prefix} ${message}`;
  
  if (data !== undefined) {
    if (typeof data === 'object') {
      try {
        fullMessage += ` ${JSON.stringify(data, null, 2)}`;
      } catch (e) {
        fullMessage += ` [Circular Reference or Non-Serializable Object]`;
      }
    } else {
      fullMessage += ` ${data}`;
    }
  }
  
  return fullMessage;
};

// ログ出力関数
export const debug = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.DEBUG) {
    console.log(formatMessage('DEBUG', message, data));
  }
};

export const info = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.INFO) {
    console.log(formatMessage('INFO', message, data));
  }
};

export const warn = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.WARN) {
    console.warn(formatMessage('WARN', message, data));
  }
};

export const error = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.ERROR) {
    console.error(formatMessage('ERROR', message, data));
  }
};

// リクエスト/レスポンスロギング用のヘルパー
export const logRequest = (method: string, path: string, body?: any) => {
  info(`→ ${method} ${path}`, body ? { body } : undefined);
};

export const logResponse = (method: string, path: string, status: number, duration: number) => {
  const level = status >= 400 ? 'ERROR' : 'INFO';
  const fn = status >= 400 ? error : info;
  fn(`← ${method} ${path} ${status} (${duration}ms)`);
};

// エラーロギング用のヘルパー
export const logError = (context: string, err: any) => {
  const errorInfo = {
    context,
    message: err?.message || 'Unknown error',
    stack: err?.stack,
    ...(err && typeof err === 'object' ? err : {})
  };
  error(`Error in ${context}`, errorInfo);
};

// 起動メッセージ
export const logStartup = (appName: string, port: number) => {
  info(`🚀 ${appName} started on port ${port}`);
};

// エクスポート（簡易版も提供）
export const log = {
  debug,
  info,
  warn,
  error,
  request: logRequest,
  response: logResponse,
  error: logError,
  startup: logStartup
};
