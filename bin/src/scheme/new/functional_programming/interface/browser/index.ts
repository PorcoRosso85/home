/**
 * index.ts
 * 
 * ブラウザインターフェースのエントリーポイント
 */

import { App } from './application/app.ts';
import { createApiClient } from './infrastructure/apiClient.ts';
import { createSchemaRepository } from './infrastructure/repositoryFactory.ts';
import { SchemaService } from './domain/service/schemaService.ts';

/**
 * アプリケーションの初期化
 */
export async function initializeApp(): Promise<void> {
  try {
    const rootElement = document.getElementById('app');
    if (!rootElement) {
      throw new Error('アプリケーションコンテナが見つかりません。id="app"の要素が必要です。');
    }
    
    // APIクライアント（コマンド実行用）
    const client = createApiClient();
    
    // スキーマリポジトリとサービスの作成
    const schemaRepository = createSchemaRepository();
    const schemaService = new SchemaService(schemaRepository);
    
    // アプリケーションの作成と初期化
    const app = new App(client, rootElement, schemaService);
    await app.initialize();
  } catch (error) {
    console.error('アプリケーション初期化エラー:', error);
  }
}

// ブラウザ環境でのみ実行される初期化コード
if (typeof window !== 'undefined') {
  window.addEventListener('DOMContentLoaded', () => {
    initializeApp().catch(error => {
      console.error('アプリケーション初期化エラー:', error);
    });
  });
}
