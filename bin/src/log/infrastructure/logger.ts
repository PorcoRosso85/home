/**
 * ロガーファクトリ
 * プラグインとオプションからロガーを作成
 */
import { Logger, LoggerOptions, LoggerPlugin, LogLevel } from "../domain/type.ts";

// デフォルトオプション
const DEFAULT_OPTIONS: LoggerOptions = {
  level: LogLevel.ERROR, // デフォルトはERRORレベル
};

// 環境からログレベルを取得
const getEnvironmentLogLevel = (): LogLevel => {
  // ブラウザ環境のwindow.LOG_LEVELを優先
  if (typeof window !== 'undefined' && (window as any).LOG_LEVEL !== undefined) {
    return (window as any).LOG_LEVEL;
  }
  
  // Node.js環境のprocess.envを次に確認
  if (typeof process !== 'undefined' && process.env?.LOG_LEVEL) {
    const level = parseInt(process.env.LOG_LEVEL, 10);
    if ([LogLevel.ERROR, LogLevel.WARN, LogLevel.INFO, LogLevel.DEBUG].includes(level)) {
      return level;
    }
  }
  
  // デフォルトはERRORレベル
  return LogLevel.ERROR;
};

/**
 * ロガーファクトリ関数
 * プラグインとオプションからロガーインスタンスを作成
 * 
 * @param plugins プラグインの配列
 * @param options ロガーのオプション
 * @returns ロガーインスタンス
 */
export const createLogger = (
  plugins: LoggerPlugin[] = [],
  options?: Partial<LoggerOptions>
): Logger => {
  // オプションの設定（デフォルトとマージ）
  const opts = { ...DEFAULT_OPTIONS, ...options };
  
  // 環境から設定されたログレベルを優先
  const envLevel = getEnvironmentLogLevel();
  const effectiveLevel = options?.level !== undefined ? options.level : envLevel;
  
  // ロガーインスタンス作成
  const logger: Logger = {
    /**
     * 指定したレベルでログを記録
     * 
     * @param level ログレベル
     * @param message ログメッセージ
     * @param data 追加データ
     */
    log: (level: LogLevel, message: string, data?: any): void => {
      // レベルフィルタリング
      if (level > effectiveLevel) {
        return;
      }
      
      // すべてのプラグインでログを処理
      for (const plugin of plugins) {
        try {
          plugin.process(level, message, data);
        } catch (err) {
          console.error(`Error in plugin ${plugin.name}:`, err);
        }
      }
    },
    
    // レベル別のログメソッド
    error: (message: string, data?: any): void => {
      logger.log(LogLevel.ERROR, message, data);
    },
    
    warn: (message: string, data?: any): void => {
      logger.log(LogLevel.WARN, message, data);
    },
    
    info: (message: string, data?: any): void => {
      logger.log(LogLevel.INFO, message, data);
    },
    
    debug: (message: string, data?: any): void => {
      logger.log(LogLevel.DEBUG, message, data);
    }
  };
  
  return logger;
};
