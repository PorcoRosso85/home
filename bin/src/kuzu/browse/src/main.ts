// 最小構成版 - DDL実行のみ
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import * as logger from '../../common/infrastructure/logger';

// ブラウザ用にログレベルを設定
(window as any).LOG_LEVEL = 4; // DEBUG level
console.log('LOG_LEVEL設定:', (window as any).LOG_LEVEL);

// loggerをテスト
console.log('Testing logger functions...');
logger.error('Test error log');
logger.warn('Test warn log');
logger.info('Test info log');
logger.debug('Test debug log');

document.addEventListener("DOMContentLoaded", async () => {
  try {
    logger.debug('Reactアプリをマウント中...');
    const rootElement = document.getElementById('root');
    if (rootElement) {
      const root = createRoot(rootElement);
      root.render(React.createElement(App));
      logger.debug('Reactアプリマウント完了');
    }
    
    logger.info('データベース初期化開始');
    
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
    
    try {
      // DDL: スキーマファイルを読み込んで実行
      logger.debug('DDLスキーマ読み込み中...');
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
        // セミコロンを追加せずに実行（既に含まれているため）
        const result = await conn.query(command);
        await result.close();
      }
      
      logger.info('DDL実行完了');
      
      // テーブル確認
      logger.debug('テーブル確認中...');
      const checkResult = await conn.query("MATCH (n:LocationURI) RETURN count(n) as count");
      const checkData = await checkResult.getAllObjects();
      logger.debug(`LocationURIノード数: ${JSON.stringify(checkData)}`);
      await checkResult.close();
      
    } finally {
      // リソースのクリーンアップはdatabase-readyイベント後に行う
      logger.debug('データベース初期化完了（接続は保持）');
    }
    
    // database-readyイベントを発火
    const event = new CustomEvent('database-ready');
    document.dispatchEvent(event);
    logger.info('database-ready イベント発火');
    
  } catch (error) {
    logger.error('初期化エラー:', error);
    throw error;
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
