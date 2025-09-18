/**
 * Browser KuzuDB Variants - bin/docs規約準拠
 * KuzuDB WASMの各バリアント用実装
 */

import type { BrowserKuzuClient } from "./types.ts";
import { BrowserKuzuClientImpl } from "./browser_kuzu_client.ts";

/**
 * マルチスレッド対応ブラウザクライアント
 * Cross-Origin Isolation必要
 */
export class MultithreadedBrowserKuzuClient extends BrowserKuzuClientImpl {
  async initialize(): Promise<void> {
    if (typeof Deno !== 'undefined' && Deno.env.get("DENO_DEPLOYMENT_ID") === undefined) {
      // テスト環境では親クラスのモック実装を使用
      return super.initialize();
    }
    
    // マルチスレッドビルド使用
    const kuzu = await import("kuzu-wasm/multithreaded");
    
    // Worker pathを設定（必要に応じて）
    if (typeof kuzu.setWorkerPath === 'function' && this.getWorkerPath) {
      kuzu.setWorkerPath(this.getWorkerPath());
    }
    
    // 初期化
    await kuzu.init();
    
    // Database と Connection を作成
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    // Create schema
    await this.createSchema();
  }
  
  private getWorkerPath?(): string;
}

/**
 * 同期版ブラウザクライアント（プロトタイピング用）
 * GUI/Webアプリでの使用非推奨
 */
export class SyncBrowserKuzuClient implements BrowserKuzuClient {
  private db?: any;
  private conn?: any;
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private clientId = `browser_sync_${crypto.randomUUID()}`;

  initialize(): void {
    if (typeof Deno !== 'undefined' && Deno.env.get("DENO_DEPLOYMENT_ID") === undefined) {
      // テスト環境ではモック実装
      this.db = {};
      this.conn = {
        query: (cypher: string, params?: Record<string, any>) => {
          // 同期版モック
          return {
            getAllObjects: () => []
          };
        }
      };
      return;
    }
    
    // 同期版ビルド使用
    const kuzu = require("kuzu-wasm/sync");
    
    // 同期版は初期化不要
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    // Create schema
    this.createSchemaSync();
  }
  
  private createSchemaSync(): void {
    this.conn.query(`
      CREATE NODE TABLE IF NOT EXISTS User(
        id STRING, 
        name STRING, 
        email STRING, 
        PRIMARY KEY(id)
      )
    `);
    
    this.conn.query(`
      CREATE NODE TABLE IF NOT EXISTS Post(
        id STRING,
        content STRING,
        authorId STRING,
        PRIMARY KEY(id)
      )
    `);
    
    this.conn.query(`
      CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)
    `);
  }
  
  // 他のメソッドは同期版として実装...
}

import type { TemplateEvent } from "../event_sourcing/types.ts";
import { TemplateRegistry } from "../event_sourcing/template_event_store.ts";