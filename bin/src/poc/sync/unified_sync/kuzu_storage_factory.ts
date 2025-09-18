/**
 * KuzuDB Storage Factory (ESM)
 * CTSモジュールをESMから使用するためのファクトリー
 * 
 * WARNING: KuzuDB Node.js版はESM非対応のため、CTSブリッジが必要
 */

import type { StorageFactory, GraphStorage } from "./test_storage_interface.ts";

export class KuzuNodeStorageFactory implements StorageFactory {
  async createStorage(): Promise<GraphStorage> {
    // WARNING: KuzuDB Node.js版はCommonJSのみサポート
    // CTSファイルを動的インポート
    const { KuzuNodeStorage } = await import("./kuzu_storage.cjs");
    
    const storage = new KuzuNodeStorage();
    await storage.initialize();
    
    return storage;
  }
}

/**
 * ブラウザ用KuzuDBストレージファクトリー
 * WARNING: ブラウザ版はESMサポートあり、Node.js版とは異なる
 */
export class KuzuBrowserStorageFactory implements StorageFactory {
  async createStorage(): Promise<GraphStorage> {
    // ブラウザ版はESMサポート
    const kuzu = await import("kuzu-wasm");
    await kuzu.init();
    
    const db = new kuzu.Database(':memory:');
    const conn = new kuzu.Connection(db);
    
    // スキーマ作成
    await this.createSchema(conn);
    
    return new KuzuBrowserStorage(conn);
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

// ブラウザ用ストレージ実装（ESM）
class KuzuBrowserStorage implements GraphStorage {
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
  
  async getLocalState(): Promise<any> {
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