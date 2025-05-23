/**
 * データベースイベント管理
 */
import * as logger from '../../../../common/infrastructure/logger';

// グローバル定義
declare global {
  type Window = {
    conn: any;
  }
}

/**
 * database-readyイベントを発火
 */
export function dispatchDatabaseReady(): void {
  const event = new CustomEvent('database-ready');
  document.dispatchEvent(event);
  logger.info('database-ready イベント発火');
}

/**
 * database-readyイベントリスナーを登録
 */
export function onDatabaseReady(handler: () => void | Promise<void>): () => void {
  const eventName = 'database-ready';
  logger.debug(`${eventName} イベントリスナーを設定します`);
  
  document.addEventListener(eventName, handler);
  
  // 初期状態でデータベースが準備済みの場合を考慮
  if (window.conn) {
    logger.debug('データベースは既に準備済み、直接ハンドラを実行します');
    handler();
  }
  
  // クリーンアップ関数を返す
  return () => {
    logger.debug(`${eventName} イベントリスナーを削除します`);
    document.removeEventListener(eventName, handler);
  };
}
