/**
 * Browser KuzuDB Client - モックフリー実装
 * ブラウザ環境専用（ESM版KuzuDB WASM使用）
 */

import type { BrowserKuzuClient, LocalState, EventSnapshot } from "../../types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";
import { createTemplateEvent, validateParams } from "../../event_sourcing/core.ts";
import { TemplateRegistry } from "../../event_sourcing/template_event_store.ts";

export class BrowserKuzuClientImpl implements BrowserKuzuClient {
  private db?: any;
  private conn?: any;
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private clientId = `browser_${crypto.randomUUID()}`;

  async initialize(): Promise<void> {
    // ブラウザ環境でのみ実行（ESM版）
    const kuzu = await import("kuzu-wasm");
    
    // Worker pathを設定（必要に応じて）
    if (typeof kuzu.setWorkerPath === 'function' && this.getWorkerPath) {
      kuzu.setWorkerPath(this.getWorkerPath());
    }
    
    // 初期化（非同期版）
    await kuzu.init();
    
    // Database と Connection を作成
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    // Create schema
    await this.createSchema();
  }
  
  // Worker pathを取得するための拡張ポイント
  private getWorkerPath?(): string;

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    await this.initialize();
    
    // Replay events from snapshot
    for (const event of snapshot.events) {
      this.events.push(event);
      await this.applyEvent(event);
    }
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }
    
    // Validate template and parameters
    const metadata = this.registry.getTemplateMetadata(template);
    const sanitizedParams = validateParams(params, metadata);
    
    // Check for injection attempts
    for (const value of Object.values(sanitizedParams)) {
      if (typeof value === 'string' && 
          (value.includes("DROP") || value.includes("DELETE") || value.includes("--"))) {
        throw new Error("Invalid parameter: potential injection attempt");
      }
    }
    
    // Create event
    const event = createTemplateEvent(template, sanitizedParams, this.clientId);
    
    // Apply to local KuzuDB
    await this.applyEvent(event);
    
    // Store event
    this.events.push(event);
    
    return event;
  }

  async getLocalState(): Promise<LocalState> {
    if (!this.conn) {
      return { users: [], posts: [], follows: [] };
    }
    
    try {
      // Get users
      const userResult = await this.conn.query(`
        MATCH (u:User)
        RETURN u.id as id, u.name as name, u.email as email
        ORDER BY u.id
      `);
      const users = userResult.getAllObjects ? userResult.getAllObjects() : [];
      
      // Get posts
      const postResult = await this.conn.query(`
        MATCH (p:Post)
        RETURN p.id as id, p.content as content, p.authorId as authorId
        ORDER BY p.id
      `);
      const posts = postResult.getAllObjects ? postResult.getAllObjects() : [];
      
      // Get follows
      const followResult = await this.conn.query(`
        MATCH (follower:User)-[:FOLLOWS]->(target:User)
        RETURN follower.id as followerId, target.id as targetId
      `);
      const follows = followResult.getAllObjects ? followResult.getAllObjects() : [];
      
      return { users, posts, follows };
    } catch (error) {
      console.error("Error getting local state:", error);
      return { users: [], posts: [], follows: [] };
    }
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  // Private methods

  private async createSchema(): Promise<void> {
    await this.conn.query(`
      CREATE NODE TABLE IF NOT EXISTS User(
        id STRING, 
        name STRING, 
        email STRING, 
        PRIMARY KEY(id)
      )
    `);
    
    await this.conn.query(`
      CREATE NODE TABLE IF NOT EXISTS Post(
        id STRING,
        content STRING,
        authorId STRING,
        PRIMARY KEY(id)
      )
    `);
    
    await this.conn.query(`
      CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)
    `);
  }

  private async applyEvent(event: TemplateEvent): Promise<void> {
    const templates: Record<string, string> = {
      CREATE_USER: `
        CREATE (u:User {
          id: $id,
          name: $name,
          email: $email
        })
      `,
      UPDATE_USER: `
        MATCH (u:User {id: $id})
        SET u.name = $name
      `,
      CREATE_POST: `
        CREATE (p:Post {
          id: $id,
          content: $content,
          authorId: $authorId
        })
      `,
      FOLLOW_USER: `
        MATCH (follower:User {id: $followerId})
        MATCH (target:User {id: $targetId})
        CREATE (follower)-[:FOLLOWS]->(target)
      `
    };
    
    const query = templates[event.template];
    if (query && this.conn) {
      await this.conn.query(query, event.params);
      
      // Notify handlers
      this.remoteEventHandlers.forEach(handler => handler(event));
    }
  }
}