// データベース初期化処理を専門化
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import * as logger from '../common/infrastructure/logger';
import { dispatchDatabaseReady } from './infrastructure/database/databaseEvent';
import { createConnection } from './infrastructure/repository/databaseConnection';
import { createSchema } from './application/usecase/createSchema';
// import { createDatabaseData } from './application/usecase/createDatabaseData';  // 最小構成のためコメントアウト
import { insertDuckVersions } from './application/usecase/insertDuckVersions';
import { env, validateEnvironment } from './infrastructure/config/variables';

// 環境変数の検証
validateEnvironment();

// ブラウザ用にログレベルを設定
(window as any).LOG_LEVEL = parseInt(env.LOG_LEVEL);

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
 * 最小構成: DuckLakeバージョンデータのみ
 */
async function initializeApp(): Promise<void> {
  // 1. データベース初期化
  const conn = await createConnection();
  
  // 2. DDL実行
  await createSchema(conn);
  
  // 3. デフォルトデータ挿入（コメントアウト - 最小構成のため）
  // await createDatabaseData.testDefault(conn);
  
  // 3. kuzuBrowseプロジェクトデータ挿入（コメントアウト - 最小構成のため）
  // await createDatabaseData.kuzuBrowse(conn);
  
  // 4. DuckLakeバージョン挿入（Phase 1確認用）
  const insertResult = await insertDuckVersions(conn);
  if ('code' in insertResult) {
    logger.error('DuckLakeバージョン挿入失敗:', insertResult.message);
  } else {
    logger.info(`DuckLakeバージョン ${insertResult.insertedCount} 件挿入完了`);
  }
  
  // 5. database-readyイベントを発火
  dispatchDatabaseReady();
  
  // 6. Reactアプリをマウント（データベース準備完了後）
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
