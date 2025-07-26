/**
 * Server KuzuDB Client
 * サーバー環境でKuzuDBインスタンスを管理
 * 
 * 責務:
 * - サーバー側でのin-memory KuzuDB管理
 * - イベント適用による状態同期
 * - クエリ実行インターフェース提供
 */

import type { TemplateEvent } from "../../event_sourcing/types.ts";
import type { LocalState, EventSnapshot } from "../../types.ts";
import type { DDLTemplateEvent } from "../../event_sourcing/ddl_types.ts";
import { isDDLEvent } from "../../event_sourcing/ddl_types.ts";
import { validateParams } from "../../event_sourcing/core.ts";
import { TemplateRegistry } from "../../event_sourcing/template_event_store.ts";
import { StateCache } from "../cache/state_cache.ts";
import { SchemaManager } from "../schema_manager.ts";
import { DDLOperationType } from "../../event_sourcing/ddl_types.ts";
import { ExtendedTemplateRegistry } from "../../event_sourcing/ddl_event_handler.ts";

export class ServerKuzuClient {
  private db?: any;
  private conn?: any;
  private events: TemplateEvent[] = [];
  private registry = new TemplateRegistry();
  private extendedRegistry = new ExtendedTemplateRegistry();
  private stateCache = new StateCache();
  private schemaManager: SchemaManager;
  private initialized = false;
  private clientId: string;

  constructor(clientId?: string) {
    this.clientId = clientId || `server_${crypto.randomUUID()}`;
    this.schemaManager = new SchemaManager(this.clientId);
  }

  async initialize(): Promise<void> {
    if (this.initialized) {
      console.warn("ServerKuzuClient already initialized");
      return;
    }

    try {
      // Use sync version for Deno
      const kuzuModule = await import("kuzu-wasm/sync");
      const kuzu = kuzuModule.default || kuzuModule;
      
      // Initialize the WASM module
      await kuzu.init();
      
      // Create in-memory database
      this.db = new kuzu.Database(':memory:');
      this.conn = new kuzu.Connection(this.db);
      
      // Create schema
      await this.createSchema();
      
      this.initialized = true;
      console.log("ServerKuzuClient initialized successfully");
    } catch (error) {
      console.error("Failed to initialize ServerKuzuClient:", error);
      throw error;
    }
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    await this.initialize();
    
    // Clear existing state
    this.events = [];
    this.stateCache.clear();
    
    // Initialize schema manager from snapshot
    await this.schemaManager.initializeFromSnapshot(
      snapshot.events,
      (query: string) => this.conn.query(query)
    );
    
    // Replay all events from snapshot
    console.log(`Replaying ${snapshot.events.length} events from snapshot`);
    for (const event of snapshot.events) {
      await this.applyEvent(event);
      this.events.push(event);
    }
  }

  async applyEvent(event: TemplateEvent | DDLTemplateEvent): Promise<void> {
    if (!this.conn) {
      throw new Error("ServerKuzuClient not initialized");
    }

    // Check if it's a DDL event
    if (isDDLEvent(event)) {
      try {
        await this.schemaManager.applyDDLEvent(
          event,
          (query: string) => this.conn.query(query)
        );
        // Store event
        this.events.push(event);
      } catch (error) {
        console.error(`Failed to apply DDL event ${event.id}:`, error);
        throw error; // DDL errors should propagate
      }
      return;
    }

    // Handle DML events
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
      `,
      INCREMENT_COUNTER: `
        MERGE (c:Counter {id: $counterId})
        ON CREATE SET c.value = COALESCE($amount, 1)
        ON MATCH SET c.value = c.value + COALESCE($amount, 1)
      `
    };
    
    const query = templates[event.template];
    if (!query) {
      console.warn(`Unknown template: ${event.template}`);
      return;
    }

    try {
      // Validate parameters using extended registry
      const metadata = this.extendedRegistry.getTemplateMetadata(event.template);
      const sanitizedParams = validateParams(event.params, metadata);
      
      // Execute query
      await this.conn.query(query, sanitizedParams);
      
      // Invalidate cache
      this.stateCache.invalidateOnEvent(event);
      
      // Store event
      this.events.push(event);
    } catch (error) {
      console.error(`Failed to apply event ${event.id}:`, error);
      // Continue processing other events
    }
  }

  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    if (!this.conn) {
      throw new Error("ServerKuzuClient not initialized");
    }

    // Basic injection prevention
    if (cypher.includes("--") || /DROP|DELETE\s+TABLE/i.test(cypher)) {
      throw new Error("Potentially dangerous query detected");
    }

    try {
      const result = await this.conn.query(cypher, params);
      
      // Convert result to plain objects
      if (result.getAllObjects) {
        return result.getAllObjects();
      }
      
      return result;
    } catch (error) {
      console.error("Query execution failed:", error);
      throw error;
    }
  }

  async getState(): Promise<LocalState> {
    if (!this.conn) {
      return { users: [], posts: [], follows: [] };
    }
    
    // Check cache first
    const cachedState = this.stateCache.getCachedState();
    if (cachedState) {
      return cachedState;
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
      
      const state = { users, posts, follows };
      
      // Cache the result
      this.stateCache.setCachedState(state);
      
      return state;
    } catch (error) {
      console.error("Failed to get state:", error);
      return { users: [], posts: [], follows: [] };
    }
  }

  getEventCount(): number {
    return this.events.length;
  }

  getEvents(): TemplateEvent[] {
    return [...this.events];
  }

  isInitialized(): boolean {
    return this.initialized;
  }

  // Schema-related methods

  getSchemaVersion(): number {
    return this.schemaManager.getSchemaVersion();
  }

  getSchemaState() {
    return this.schemaManager.getCurrentSchema();
  }

  hasTable(tableName: string): boolean {
    return this.schemaManager.hasTable(tableName);
  }

  hasColumn(tableName: string, columnName: string): boolean {
    return this.schemaManager.hasColumn(tableName, columnName);
  }

  getTableSchema(tableName: string) {
    return this.schemaManager.getTableSchema(tableName);
  }

  getSchemaSyncState() {
    return this.schemaManager.getSyncState();
  }

  async resolveSchemaConflict(
    conflictId: string,
    resolution: "APPLY_FIRST" | "APPLY_LAST" | "MANUAL"
  ): Promise<void> {
    await this.schemaManager.resolveConflict(
      conflictId,
      resolution,
      (query: string) => this.conn.query(query)
    );
  }

  // DDL Event Creation

  createDDLEvent(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): DDLTemplateEvent {
    return this.schemaManager.createDDLEvent(ddlType, params);
  }

  async applyDDLEvent(event: DDLTemplateEvent): Promise<void> {
    await this.applyEvent(event);
  }

  getAppliedDDLs(): DDLTemplateEvent[] {
    return this.schemaManager.getAppliedDDLs();
  }

  getPendingDDLs(): DDLTemplateEvent[] {
    return this.schemaManager.getPendingDDLs();
  }

  validateDDL(event: DDLTemplateEvent): { valid: boolean; errors: string[] } {
    return this.schemaManager.validateDDL(event);
  }

  // Template Support

  hasTemplate(template: string): boolean {
    return this.extendedRegistry.hasTemplate(template);
  }

  isDDLTemplate(template: string): boolean {
    return this.extendedRegistry.isDDLTemplate(template);
  }

  isDMLTemplate(template: string): boolean {
    return this.extendedRegistry.isDMLTemplate(template);
  }

  getTemplateMetadata(template: string): any {
    return this.extendedRegistry.getTemplateMetadata(template);
  }

  // Private methods

  private async createSchema(): Promise<void> {
    // Check current schema state
    const schemaState = this.schemaManager.getCurrentSchema();
    
    // Create default schema if no tables exist
    if (Object.keys(schemaState.nodeTables).length === 0) {
      // Create User node table
      if (!this.schemaManager.hasTable("User")) {
        await this.conn.query(`
          CREATE NODE TABLE IF NOT EXISTS User(
            id STRING, 
            name STRING, 
            email STRING, 
            PRIMARY KEY(id)
          )
        `);
      }
      
      // Create Post node table
      if (!this.schemaManager.hasTable("Post")) {
        await this.conn.query(`
          CREATE NODE TABLE IF NOT EXISTS Post(
            id STRING,
            content STRING,
            authorId STRING,
            PRIMARY KEY(id)
          )
        `);
      }
      
      // Create FOLLOWS relationship table
      if (!this.schemaManager.hasTable("FOLLOWS")) {
        await this.conn.query(`
          CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)
        `);
      }
      
      // Create Counter node table
      if (!this.schemaManager.hasTable("Counter")) {
        await this.conn.query(`
          CREATE NODE TABLE IF NOT EXISTS Counter(
            id STRING,
            value INT64,
            PRIMARY KEY(id)
          )
        `);
      }
      
      console.log("Default database schema created");
    } else {
      console.log(`Schema already exists with ${Object.keys(schemaState.nodeTables).length} node tables and ${Object.keys(schemaState.edgeTables).length} edge tables`);
    }
  }
}