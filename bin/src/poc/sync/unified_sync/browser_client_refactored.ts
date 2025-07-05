/**
 * Browser Client Refactored - モック最小化
 * ストレージを注入可能な設計
 */

import type { EventSnapshot } from "./types.ts";
import type { TemplateEvent } from "../event_sourcing/types.ts";
import { createTemplateEvent, validateParams } from "../event_sourcing/core.ts";
import { TemplateRegistry } from "../event_sourcing/template_event_store.ts";
import type { GraphStorage, LocalState } from "./test_storage_interface.ts";

// ストレージファクトリー
export interface StorageFactory {
  createStorage(): Promise<GraphStorage>;
}

// KuzuDB実装（ブラウザ環境）
export class KuzuStorageFactory implements StorageFactory {
  async createStorage(): Promise<GraphStorage> {
    const kuzu = await import("kuzu-wasm");
    await kuzu.init();
    
    const db = new kuzu.Database(':memory:');
    const conn = new kuzu.Connection(db);
    
    // スキーマ作成
    await this.createSchema(conn);
    
    return new KuzuGraphStorage(conn);
  }
  
  private async createSchema(conn: any): Promise<void> {
    await conn.query(`
      CREATE NODE TABLE IF NOT EXISTS User(
        id STRING, name STRING, email STRING, PRIMARY KEY(id)
      )
    `);
    await conn.query(`
      CREATE NODE TABLE IF NOT EXISTS Post(
        id STRING, content STRING, authorId STRING, PRIMARY KEY(id)
      )
    `);
    await conn.query(`
      CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)
    `);
  }
}

// KuzuDBストレージアダプター
class KuzuGraphStorage implements GraphStorage {
  constructor(private conn: any) {}
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<any> {
    const queries: Record<string, string> = {
      CREATE_USER: `CREATE (u:User {id: $id, name: $name, email: $email})`,
      UPDATE_USER: `MATCH (u:User {id: $id}) SET u.name = $name`,
      CREATE_POST: `CREATE (p:Post {id: $id, content: $content, authorId: $authorId})`,
      FOLLOW_USER: `
        MATCH (follower:User {id: $followerId})
        MATCH (target:User {id: $targetId})
        CREATE (follower)-[:FOLLOWS]->(target)
      `
    };
    
    const query = queries[template];
    if (query) {
      await this.conn.query(query, params);
    }
    
    return { template, params, timestamp: Date.now() };
  }
  
  async getLocalState(): Promise<LocalState> {
    const userResult = await this.conn.query(`
      MATCH (u:User) RETURN u.id as id, u.name as name, u.email as email
    `);
    const users = await userResult.getAllObjects();
    
    const postResult = await this.conn.query(`
      MATCH (p:Post) RETURN p.id as id, p.content as content, p.authorId as authorId
    `);
    const posts = await postResult.getAllObjects();
    
    const followResult = await this.conn.query(`
      MATCH (follower:User)-[:FOLLOWS]->(target:User)
      RETURN follower.id as followerId, target.id as targetId
    `);
    const follows = await followResult.getAllObjects();
    
    return { users, posts, follows };
  }
}

// リファクタリングされたブラウザクライアント
export class BrowserClientRefactored {
  private storage?: GraphStorage;
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private clientId = `browser_${crypto.randomUUID()}`;
  
  constructor(private storageFactory: StorageFactory) {}
  
  async initialize(): Promise<void> {
    this.storage = await this.storageFactory.createStorage();
  }
  
  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    if (!this.storage) {
      throw new Error("Client not initialized");
    }
    
    // テンプレート検証
    const metadata = this.registry.getTemplateMetadata(template);
    const sanitizedParams = validateParams(params, metadata);
    
    // インジェクション対策
    for (const value of Object.values(sanitizedParams)) {
      if (typeof value === 'string' && 
          (value.includes("DROP") || value.includes("DELETE") || value.includes("--"))) {
        throw new Error("Invalid parameter: potential injection attempt");
      }
    }
    
    // イベント作成
    const event = createTemplateEvent(template, sanitizedParams, this.clientId);
    
    // ストレージに適用
    await this.storage.executeTemplate(template, sanitizedParams);
    
    // イベント記録
    this.events.push(event);
    
    // ハンドラー通知
    this.remoteEventHandlers.forEach(handler => handler(event));
    
    return event;
  }
  
  async getLocalState(): Promise<LocalState> {
    if (!this.storage) {
      return { users: [], posts: [], follows: [] };
    }
    return this.storage.getLocalState();
  }
  
  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }
}