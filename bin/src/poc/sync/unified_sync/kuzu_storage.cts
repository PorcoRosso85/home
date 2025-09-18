/**
 * KuzuDB Storage Implementation (CommonJS)
 * 
 * WARNING: KuzuDB Node.js版はCommonJSのみサポート（公式ドキュメントより）
 * "It is distributed as a CommonJS module rather than an ES module to maximize compatibility"
 * 
 * このファイルは.ctsとしてCommonJSモジュールとして動作します
 */

import type { GraphStorage, LocalState } from "./test_storage_interface.js";

// CommonJSでKuzuDB Node.js版を読み込む
const kuzu = require("kuzu-wasm/nodejs");

export class KuzuNodeStorage implements GraphStorage {
  private db: any;
  private conn: any;
  private initialized = false;

  async initialize(): Promise<void> {
    if (this.initialized) return;
    
    // WARNING: Node.js版はCommonJSのみ対応
    await kuzu.init();
    
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    // スキーマ作成
    await this.createSchema();
    this.initialized = true;
  }

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

  async executeTemplate(template: string, params: Record<string, any>): Promise<any> {
    if (!this.initialized) {
      throw new Error("Storage not initialized");
    }

    const queries: Record<string, string> = {
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

    const query = queries[template];
    if (!query) {
      throw new Error(`Unknown template: ${template}`);
    }

    await this.conn.query(query, params);
    
    return {
      template,
      params,
      timestamp: Date.now()
    };
  }

  async getLocalState(): Promise<LocalState> {
    if (!this.initialized) {
      return { users: [], posts: [], follows: [] };
    }

    try {
      // ユーザー取得
      const userResult = await this.conn.query(`
        MATCH (u:User)
        RETURN u.id as id, u.name as name, u.email as email
        ORDER BY u.id
      `);
      const users = userResult.getAllObjects ? userResult.getAllObjects() : [];
      
      // 投稿取得
      const postResult = await this.conn.query(`
        MATCH (p:Post)
        RETURN p.id as id, p.content as content, p.authorId as authorId
        ORDER BY p.id
      `);
      const posts = postResult.getAllObjects ? postResult.getAllObjects() : [];
      
      // フォロー関係取得
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

  async close(): Promise<void> {
    if (this.conn) {
      // KuzuDBのクリーンアップ
      this.conn = null;
      this.db = null;
      this.initialized = false;
    }
  }
}

// CommonJSエクスポート
module.exports = { KuzuNodeStorage };