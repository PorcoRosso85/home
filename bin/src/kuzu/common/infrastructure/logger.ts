/**
 * アプリケーション全体で使用するロガー関数
 * 環境変数に基づいてログレベルを制御
 */
import { DEBUG } from './variables';

// タイムスタンプを取得する関数
const getTimestamp = () => {
  const now = new Date();
  return `[${now.toISOString()}]`;
};

// データのシリアライズ関数（最低限の実装）
const formatData = (data?: any): string => {
  if (data === undefined) return '';
  
  try {
    // オブジェクトや配列の場合はJSON文字列に変換
    if (typeof data === 'object' && data !== null) {
      return ` ${JSON.stringify(data, null, 2)}`;
    }
    // それ以外はそのまま文字列として返す
    return ` ${data}`;
  } catch (error) {
    return ` [データをシリアライズできません: ${(error as Error).message}]`;
  }
};

// 各ログレベルの関数
export const debug = (message: string, data?: any) => {
  if (DEBUG) {
    console.debug(`${getTimestamp()}[DEBUG] ${message}${formatData(data)}`);
  }
};

export const info = (message: string, data?: any) => {
  console.info(`${getTimestamp()}[INFO] ${message}${formatData(data)}`);
};

export const warn = (message: string, data?: any) => {
  console.warn(`${getTimestamp()}[WARN] ${message}${formatData(data)}`);
};

export const error = (message: string, data?: any) => {
  console.error(`${getTimestamp()}[ERROR] ${message}${formatData(data)}`);
};
