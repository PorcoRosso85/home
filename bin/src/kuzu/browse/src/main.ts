// データベース初期化処理を専門化
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import * as logger from '../../common/infrastructure/logger';
import { dispatchDatabaseReady } from './infrastructure/database/databaseEvent';
import { useDmlQueries } from './infrastructure/dml/useDmlQueries';

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
 * データベースを初期化
 */
async function initializeDatabase(): Promise<void> {
  logger.info('データベース初期化開始');
  
  try {
    // Kuzu-Wasmのロード
    const kuzuWasm = await import("../node_modules/kuzu-wasm");
    const kuzu = kuzuWasm.default || kuzuWasm;
    
    // グローバルにkuzuオブジェクトを設定
    window.kuzu = kuzu;
    
    // データベースと接続を作成し、グローバルに保存
    logger.debug('データベース作成中...');
    const db = new kuzu.Database("");
    const conn = new kuzu.Connection(db);
    
    // グローバルに接続も保存
    window.db = db;
    window.conn = conn;
    
    return conn;
  } catch (error) {
    logger.error('データベース初期化エラー:', error);
    throw error;
  }
}

/**
 * DDLスキーマを実行
 */
async function executeDDL(conn: any): Promise<void> {
  logger.debug('DDLスキーマ読み込み中...');
  
  try {
    const ddlResponse = await fetch('/ddl/schema.cypher');
    const ddlContent = await ddlResponse.text();
    logger.debug(`DDL内容: ${ddlContent.substring(0, 100)}...`);
    
    // DDLコマンドを分割して実行
    const lines = ddlContent.split('\n');
    let currentCommand = '';
    const ddlCommands = [];
    
    for (const line of lines) {
      // コメント行や空行をスキップ
      if (line.trim().startsWith('--') || line.trim().startsWith('//') || line.trim() === '') {
        continue;
      }
      
      // 現在のコマンドに行を追加
      currentCommand += line.trim() + ' ';
      
      // セミコロンで終わる行でコマンドを確定
      if (line.trim().endsWith(';')) {
        if (currentCommand.trim()) {
          ddlCommands.push(currentCommand.trim());
        }
        currentCommand = '';
      }
    }
    
    // 最後にセミコロンがない場合のコマンドも追加
    if (currentCommand.trim()) {
      ddlCommands.push(currentCommand.trim());
    }
    
    logger.debug(`DDLコマンド数: ${ddlCommands.length}`);
    
    for (const command of ddlCommands) {
      logger.debug(`DDL実行中: ${command.substring(0, 50)}...`);
      const result = await conn.query(command);
      await result.close();
    }
    
    logger.info('DDL実行完了');
  } catch (error) {
    logger.error('DDL実行エラー:', error);
    throw error;
  }
}

/**
 * DMLデータを挿入
 */
async function insertSampleData(conn: any): Promise<void> {
  logger.debug('DML実行中...');
  
  try {
    // DML実行ユーティリティから関数をインポート
    const { insertSampleLocationURI } = await import('./infrastructure/dml/dmlUtils');
    
    // サンプルデータを挿入
    await insertSampleLocationURI(conn);
    
    // テーブル確認
    logger.debug('テーブル確認中...');
    const checkResult = await conn.query("MATCH (n:LocationURI) RETURN count(n) as count");
    const checkData = await checkResult.getAllObjects();
    logger.debug(`LocationURIノード数: ${JSON.stringify(checkData)}`);
    await checkResult.close();
    
    logger.debug('データベース初期化完了（接続は保持）');
  } catch (error) {
    logger.error('DML実行エラー:', error);
    throw error;
  }
}

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
    const conn = await initializeDatabase();
    
    // 2. DDL実行
    await executeDDL(conn);
    
    // 3. サンプルデータ挿入
    await insertSampleData(conn);
    
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
