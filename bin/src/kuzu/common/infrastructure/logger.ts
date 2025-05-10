/**
 * アプリケーション全体で使用するロガー関数
 * 環境変数に基づいてログレベルを制御
 */
import { LOG_LEVEL, LogLevel } from './variables';

// タイムスタンプを取得する関数
const getTimestamp = () => {
  const now = new Date();
  return `[${now.toISOString()}]`;
};

// 各ログレベルの関数
export const debug = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.DEBUG) {
    console.debug(`${getTimestamp()}[DEBUG] ${message}`, data ?? '');
  }
};

export const info = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.INFO) {
    console.info(`${getTimestamp()}[INFO] ${message}`, data ?? '');
  }
};

export const warn = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.WARN) {
    console.warn(`${getTimestamp()}[WARN] ${message}`, data ?? '');
  }
};

export const error = (message: string, data?: any) => {
  if (LOG_LEVEL >= LogLevel.ERROR) {
    console.error(`${getTimestamp()}[ERROR] ${message}`, data ?? '');
  }
};
