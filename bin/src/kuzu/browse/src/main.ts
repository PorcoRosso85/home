// データベース初期化処理を専門化
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import * as logger from '../../common/infrastructure/logger';
import { dispatchDatabaseReady } from './infrastructure/database/databaseEvent';
import { createConnection } from './infrastructure/repository/databaseConnection';
import { createSchema } from './application/usecase/createSchema';
import { createDatabaseData } from './application/usecase/createDatabaseData';

// ブラウザ用にログレベルを設定
// import.meta.env.LOG_LEVELから環境変数を読み込む（build.tsで設定）
const defaultLogLevel = 3; // INFO level 
(window as any).LOG_LEVEL = import.meta.env.LOG_LEVEL ? parseInt(import.meta.env.LOG_LEVEL) : defaultLogLevel;
logger.debug('LOG_LEVEL設定:', (window as any).LOG_LEVEL);

// loggerをテスト
logger.debug('Testing logger functions...');
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
  // 1. データベース初期化
  const conn = await createConnection();
  
  // 2. DDL実行
  await createSchema(conn);
  
  // 3. デフォルトデータ挿入
  // await createDatabaseData.testDefault(conn);
  
  // 3. kuzuBrowseプロジェクトデータ挿入
  await createDatabaseData.kuzuBrowse(conn);
  
  // 4. database-readyイベントを発火
  dispatchDatabaseReady();
  
  // 5. Reactアプリをマウント（データベース準備完了後）
  logger.debug('Reactアプリをマウント中...');
  mountReactApp();
}

document.addEventListener("DOMContentLoaded", async () => {
  await initializeApp();
});

// グローバル定義
declare global {
  type Window = {
    kuzu: any;
    db: any;
    conn: any;
  }
}
