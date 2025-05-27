/**
 * KuzuDB Graph Browser エントリポイント
 */
import React from 'react';
import { createRoot } from 'react-dom/client';
import App from './interface/App';
import { dispatchDatabaseReady } from './infrastructure/database/databaseEvent';

/**
 * アプリケーションの初期化
 */
const initApp = () => {
  // ルート要素の作成またはDOMから取得
  let rootElement = document.getElementById('app');
  
  if (!rootElement) {
    rootElement = document.createElement('div');
    rootElement.id = 'app';
    document.body.appendChild(rootElement);
  }
  
  // グローバルデータベースオブジェクトの確認と設定
  // 実際のKuzuDB接続はここで設定される想定
  if (!window.conn) {
    console.warn('データベース接続が見つかりません。データベース機能は制限されます。');
    
    // 開発用ダミー接続（実際のアプリケーションでは削除する）
    // 本番環境では、KuzuDBの初期化スクリプトがロード完了後にwindow.connを設定し、
    // dispatchDatabaseReady()を呼び出す必要がある
    window.conn = {};
    setTimeout(() => {
      dispatchDatabaseReady();
    }, 500);
  }
  
  // Reactアプリケーションのマウント
  const root = createRoot(rootElement);
  root.render(
    <React.StrictMode>
      <App />
    </React.StrictMode>
  );
  
  console.log('KuzuDB Graph Browser アプリケーションが初期化されました');
};

// DOMの読み込み完了後にアプリケーションを初期化
if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', initApp);
} else {
  initApp();
}
