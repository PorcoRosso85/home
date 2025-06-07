/**
 * Deno環境用のロガー変数定義
 * Kuzuからの移植版
 */

// ログレベル定義
export const enum LogLevel {
  ERROR = 1,
  WARN = 2,
  INFO = 3,
  DEBUG = 4
}

// 環境変数からログレベルを取得（デフォルト: DEBUG）
const getLogLevel = (): LogLevel => {
  const level = Deno.env.get('LOG_LEVEL');
  if (!level) return LogLevel.DEBUG;
  
  const numLevel = parseInt(level, 10);
  if (isNaN(numLevel) || numLevel < 1 || numLevel > 4) {
    console.warn(`Invalid LOG_LEVEL: ${level}, using DEBUG level`);
    return LogLevel.DEBUG;
  }
  
  return numLevel as LogLevel;
};

export const LOG_LEVEL = getLogLevel();

// ログレベル名を取得
export const getLogLevelName = (level: LogLevel): string => {
  switch (level) {
    case LogLevel.ERROR: return 'ERROR';
    case LogLevel.WARN: return 'WARN';
    case LogLevel.INFO: return 'INFO';
    case LogLevel.DEBUG: return 'DEBUG';
    default: return 'UNKNOWN';
  }
};

console.info(`[Logger] Initialized with level: ${getLogLevelName(LOG_LEVEL)}`);
