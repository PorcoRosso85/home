// データベース初期化処理を専門化
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import * as logger from '../../common/infrastructure/logger';
import { dispatchDatabaseReady } from './infrastructure/database/databaseEvent';
import { createConnection } from './infrastructure/repository/databaseConnection';
import { createSchema } from './application/usecase/createSchema';
import { seedDefaultData } from './application/usecase/seedDefaultData';

// ブラウザ用にログレベルを設定
(window as any).LOG_LEVEL = 4; // DEBUG level
console.log('LOG_LEVEL設定:', (window as any).LOG_LEVEL);

// loggerをテスト
console.log('Testing logger functions...');
logger.error('Test error log');
logger.warn('Test warn log');
logger.info('Test info log');
logger.debug('Test debug log');

/**
 * Reactアプリをマウント
 */
function mountReactApp(): void {
  const rootElement = document.getElementById('root');
  if (rootElement) {
    const root = createRoot(rootElement);
    root.render(React.createElement(App));
    logger.debug('Reactアプリマウント完了');
  }
}

/**
 * アプリの初期化処理
 */
async function initializeApp(): Promise<void> {
  logger.debug('Reactアプリをマウント中...');
  mountReactApp();
  
  try {
    // 1. データベース初期化
    const conn = await createConnection();
    
    // 2. DDL実行
    await createSchema(conn);
    
    // 3. デフォルトデータ挿入
    await seedDefaultData(conn);
    
    // 4. database-readyイベントを発火
    dispatchDatabaseReady();
    
  } catch (error) {
    logger.error('初期化エラー:', error);
    throw error;
  }
}

document.addEventListener("DOMContentLoaded", async () => {
  try {
    await initializeApp();
  } catch (error) {
    logger.error('DOMContentLoadedエラー:', error);
  }
});

// グローバル定義
declare global {
  interface Window {
    kuzu: any;
    db: any;
    conn: any;
  }
}
