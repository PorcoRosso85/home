/**
 * アプリケーション全体で使用するロガー関数
 * 規約準拠: デフォルト値禁止、LOG_LEVELを直接importで使用
 */
import { LogLevel, LOG_LEVEL } from './variables.ts';

// タイムスタンプを取得する関数
const getTimestamp = () => {
  const now = new Date();
  return `[${now.toISOString()}]`;
};

// 各ログレベルの関数（デフォルト引数を削除）
export const debug = (message: string, data: any) => {
  if (LOG_LEVEL >= LogLevel.DEBUG) {
    console.info(`${getTimestamp()}[DEBUG] ${message}`, data);
  }
};

export const info = (message: string, data: any) => {
  if (LOG_LEVEL >= LogLevel.INFO) {
    console.info(`${getTimestamp()}[INFO] ${message}`, data);
  }
};

export const warn = (message: string, data: any) => {
  if (LOG_LEVEL >= LogLevel.WARN) {
    console.warn(`${getTimestamp()}[WARN] ${message}`, data);
  }
};

export const error = (message: string, data: any) => {
  if (LOG_LEVEL >= LogLevel.ERROR) {
    console.error(`${getTimestamp()}[ERROR] ${message}`, data);
  }
};

// dataが不要な場合の関数（オーバーロード）
export const debugSimple = (message: string) => {
  if (LOG_LEVEL >= LogLevel.DEBUG) {
    console.info(`${getTimestamp()}[DEBUG] ${message}`);
  }
};

export const infoSimple = (message: string) => {
  if (LOG_LEVEL >= LogLevel.INFO) {
    console.info(`${getTimestamp()}[INFO] ${message}`);
  }
};

export const warnSimple = (message: string) => {
  if (LOG_LEVEL >= LogLevel.WARN) {
    console.warn(`${getTimestamp()}[WARN] ${message}`);
  }
};

export const errorSimple = (message: string) => {
  if (LOG_LEVEL >= LogLevel.ERROR) {
    console.error(`${getTimestamp()}[ERROR] ${message}`);
  }
};
