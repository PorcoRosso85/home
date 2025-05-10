/**
 * アプリケーション全体で使用するロガー関数
 * 環境変数に基づいてログレベルを制御
 */
import { LogLevel } from './variables';

// 動的にLOG_LEVELを取得する関数
const getLogLevel = () => {
  // ブラウザ環境のwindow.LOG_LEVELを優先
  if (typeof window !== 'undefined' && (window as any).LOG_LEVEL !== undefined) {
    return (window as any).LOG_LEVEL;
  }
  
  // Node.js環境のprocess.envを次に確認
  if (typeof process !== 'undefined' && process.env?.LOG_LEVEL) {
    return parseInt(process.env.LOG_LEVEL, 10);
  }
  
  // デフォルトはERRORレベル
  return LogLevel.ERROR;
};

// タイムスタンプを取得する関数
const getTimestamp = () => {
  const now = new Date();
  return `[${now.toISOString()}]`;
};

// 各ログレベルの関数
export const debug = (message: string, data?: any) => {
  const currentLevel = getLogLevel();
  if (currentLevel >= LogLevel.DEBUG) {
    console.info(`${getTimestamp()}[DEBUG] ${message}`, data ?? '');
  }
};

export const info = (message: string, data?: any) => {
  const currentLevel = getLogLevel();
  if (currentLevel >= LogLevel.INFO) {
    console.info(`${getTimestamp()}[INFO] ${message}`, data ?? '');
  }
};

export const warn = (message: string, data?: any) => {
  const currentLevel = getLogLevel();
  if (currentLevel >= LogLevel.WARN) {
    console.warn(`${getTimestamp()}[WARN] ${message}`, data ?? '');
  }
};

export const error = (message: string, data?: any) => {
  const currentLevel = getLogLevel();
  if (currentLevel >= LogLevel.ERROR) {
    console.error(`${getTimestamp()}[ERROR] ${message}`, data ?? '');
  }
};
