/**
 * Universal KuzuDB wrapper for both Browser and Server (Node.js/Bun) environments
 */

interface KuzuModule {
  Database: any;
  Connection: any;
  close: () => Promise<void>;
}

interface QueryResult {
  getAllObjects: () => Promise<any[]>;
  toString: () => Promise<string>;
  close: () => Promise<void>;
}

export class UniversalKuzu {
  private kuzu: KuzuModule | null = null;
  private db: any = null;
  private conn: any = null;
  private isInitialized = false;

  /**
   * Initialize KuzuDB based on the current environment
   */
  async initialize(memorySize: number = 1 << 28 /* 256MB */): Promise<void> {
    if (this.isInitialized) {
      return;
    }

    // Detect environment and load appropriate module
    if (typeof window !== 'undefined') {
      // Browser environment
      console.log('🌐 Initializing KuzuDB for browser...');
      // @ts-ignore - Dynamic import for browser
      this.kuzu = await import('kuzu-wasm');
    } else if (typeof process !== 'undefined' || typeof Bun !== 'undefined') {
      // Node.js or Bun environment
      console.log('🖥️ Initializing KuzuDB for server (Node.js/Bun)...');
      // @ts-ignore - Dynamic require for Node.js/Bun
      this.kuzu = require('kuzu-wasm/nodejs');
    } else {
      throw new Error('Unknown runtime environment');
    }

    // Create database and connection
    this.db = new this.kuzu.Database(':memory:', memorySize);
    this.conn = new this.kuzu.Connection(this.db, 4);
    this.isInitialized = true;
  }

  /**
   * Execute a query
   */
  async query(cypher: string): Promise<QueryResult> {
    if (!this.isInitialized) {
      throw new Error('KuzuDB not initialized. Call initialize() first.');
    }
    return await this.conn.query(cypher);
  }

  /**
   * Execute a query and return all results as objects
   */
  async queryObjects(cypher: string): Promise<any[]> {
    const result = await this.query(cypher);
    const objects = await result.getAllObjects();
    await result.close();
    return objects;
  }

  /**
   * Execute a query and return the first result
   */
  async queryOne(cypher: string): Promise<any | null> {
    const results = await this.queryObjects(cypher);
    return results.length > 0 ? results[0] : null;
  }

  /**
   * Execute multiple queries in sequence
   */
  async executeMany(queries: string[]): Promise<void> {
    for (const query of queries) {
      const result = await this.query(query);
      await result.close();
    }
  }

  /**
   * Create a schema from Cypher statements
   */
  async createSchema(schemaStatements: string[]): Promise<void> {
    console.log('📊 Creating schema...');
    for (const statement of schemaStatements) {
      if (statement.trim()) {
        console.log(`  Executing: ${statement}`);
        const result = await this.query(statement);
        await result.close();
      }
    }
  }

  /**
   * Load data from Cypher statements
   */
  async loadData(dataStatements: string[]): Promise<void> {
    console.log('📥 Loading data...');
    for (const statement of dataStatements) {
      if (statement.trim()) {
        const result = await this.query(statement);
        await result.close();
      }
    }
  }

  /**
   * Begin a transaction
   */
  async beginTransaction(): Promise<void> {
    await this.query('BEGIN TRANSACTION');
  }

  /**
   * Commit a transaction
   */
  async commit(): Promise<void> {
    await this.query('COMMIT');
  }

  /**
   * Rollback a transaction
   */
  async rollback(): Promise<void> {
    await this.query('ROLLBACK');
  }

  /**
   * Clean up resources
   */
  async cleanup(): Promise<void> {
    if (!this.isInitialized) {
      return;
    }

    console.log('🧹 Cleaning up KuzuDB resources...');
    
    if (this.conn) {
      await this.conn.close();
      this.conn = null;
    }
    
    if (this.db) {
      await this.db.close();
      this.db = null;
    }
    
    if (this.kuzu) {
      await this.kuzu.close();
      this.kuzu = null;
    }
    
    this.isInitialized = false;
  }

  /**
   * Check if running in browser
   */
  static isBrowser(): boolean {
    return typeof window !== 'undefined';
  }

  /**
   * Check if running in Node.js
   */
  static isNode(): boolean {
    return typeof process !== 'undefined' && !UniversalKuzu.isBun();
  }

  /**
   * Check if running in Bun
   */
  static isBun(): boolean {
    return typeof Bun !== 'undefined';
  }

  /**
   * Get runtime environment name
   */
  static getEnvironment(): string {
    if (UniversalKuzu.isBrowser()) return 'browser';
    if (UniversalKuzu.isBun()) return 'bun';
    if (UniversalKuzu.isNode()) return 'node';
    return 'unknown';
  }
}