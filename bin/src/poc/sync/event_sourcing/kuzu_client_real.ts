/**
 * Real KuzuDB WASM Client (ESM)
 * 実際のKuzuDB WASMクライアント実装
 */

import { Database, Connection } from "kuzu-wasm";

// ========== 型定義 ==========

export interface TemplateEvent {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
}

export interface QueryResult {
  rows: any[];
  columns: string[];
}

// ========== KuzuDB Event Client ==========

export class KuzuEventClient {
  private db?: Database;
  private conn?: Connection;
  private clientId: string;
  private events: TemplateEvent[] = [];
  private templates = {
    CREATE_USER: `
      CREATE (u:User {
        id: $id,
        name: $name,
        email: $email,
        createdAt: $createdAt
      })
      RETURN u
    `,
    UPDATE_USER: `
      MATCH (u:User {id: $id})
      SET u.name = $name, u.email = $email
      RETURN u
    `,
    FOLLOW_USER: `
      MATCH (follower:User {id: $followerId})
      MATCH (target:User {id: $targetId})
      CREATE (follower)-[:FOLLOWS {since: $since}]->(target)
      RETURN follower, target
    `,
    CREATE_POST: `
      CREATE (p:Post {
        id: $id,
        content: $content,
        authorId: $authorId,
        createdAt: $createdAt
      })
      RETURN p
    `,
    DELETE_POST: `
      MATCH (p:Post {id: $id})
      DELETE p
    `
  };

  constructor(clientId: string) {
    this.clientId = clientId;
  }

  async initialize(): Promise<void> {
    // Dynamic import for KuzuDB WASM initialization
    const kuzu = await import("kuzu-wasm");
    const { default: kuzuModule } = kuzu;
    
    // Initialize if needed
    if (typeof kuzuModule.init === 'function') {
      await kuzuModule.init();
    }
    
    // Use the module's exports
    const Database = kuzuModule.Database || kuzu.Database;
    const Connection = kuzuModule.Connection || kuzu.Connection;
    
    this.db = new Database(':memory:');
    this.conn = new Connection(this.db);
    
    // Create schema
    await this.conn.query(`
      CREATE NODE TABLE User(
        id STRING, 
        name STRING, 
        email STRING, 
        createdAt STRING, 
        PRIMARY KEY(id)
      )
    `);
    
    await this.conn.query(`
      CREATE NODE TABLE Post(
        id STRING,
        content STRING,
        authorId STRING,
        createdAt STRING,
        PRIMARY KEY(id)
      )
    `);
    
    await this.conn.query(`
      CREATE REL TABLE FOLLOWS(FROM User TO User, since STRING)
    `);
    
    await this.conn.query(`
      CREATE REL TABLE AUTHORED(FROM User TO Post)
    `);
  }

  async executeTemplate(templateName: string, params: Record<string, any>): Promise<TemplateEvent> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }
    
    const template = this.templates[templateName];
    if (!template) {
      throw new Error(`Unknown template: ${templateName}`);
    }
    
    // Execute in KuzuDB
    await this.conn.query(template, params);
    
    // Create event
    const event: TemplateEvent = {
      id: `evt_${crypto.randomUUID()}`,
      template: templateName,
      params: { ...params },
      timestamp: Date.now(),
      clientId: this.clientId,
      checksum: this.calculateChecksum(templateName, params)
    };
    
    this.events.push(event);
    return event;
  }

  private calculateChecksum(template: string, params: Record<string, any>): string {
    const content = JSON.stringify({ template, params });
    let hash = 0;
    for (let i = 0; i < content.length; i++) {
      const char = content.charCodeAt(i);
      hash = ((hash << 5) - hash) + char;
      hash = hash & hash;
    }
    return Math.abs(hash).toString(16).padEnd(32, '0');
  }

  async getUsers(): Promise<any[]> {
    if (!this.conn) return [];
    
    const result = await this.conn.query(`
      MATCH (u:User)
      RETURN u.id, u.name, u.email
      ORDER BY u.id
    `);
    
    return result.getAllObjects();
  }

  async getPosts(): Promise<any[]> {
    if (!this.conn) return [];
    
    const result = await this.conn.query(`
      MATCH (p:Post)
      RETURN p.id, p.content, p.authorId
      ORDER BY p.id
    `);
    
    return result.getAllObjects();
  }

  async getFollowers(userId: string): Promise<any[]> {
    if (!this.conn) return [];
    
    const result = await this.conn.query(`
      MATCH (follower:User)-[:FOLLOWS]->(u:User {id: $userId})
      RETURN follower.id, follower.name
    `, { userId });
    
    return result.getAllObjects();
  }

  getEvents(): TemplateEvent[] {
    return [...this.events];
  }

  hasExecutedTemplate(templateName: string): boolean {
    return this.events.some(e => e.template === templateName);
  }
}