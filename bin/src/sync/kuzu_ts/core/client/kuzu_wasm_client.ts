/**
 * KuzuDB WASM Client - モックフリー実装
 * WASM版KuzuDB使用（Deno環境での実行）
 * TODO: 将来的にブラウザ環境のサポートを追加する際は、
 * Worker APIの互換性やESMローダーの違いを考慮する必要がある
 */

import type { KuzuWasmClient, LocalState, EventSnapshot } from "../../types.ts";
import type { TemplateEvent } from "../../event_sourcing/types.ts";
import type { DDLTemplateEvent } from "../../event_sourcing/ddl_types.ts";
import { isDDLEvent, DDLOperationType } from "../../event_sourcing/ddl_types.ts";
import { createTemplateEvent, validateParams } from "../../event_sourcing/core.ts";
import { TemplateRegistry } from "../../event_sourcing/template_event_store.ts";
import { StateCache } from "../cache/state_cache.ts";
import { SchemaManager } from "../schema_manager.ts";
import { ExtendedTemplateRegistry } from "../../event_sourcing/ddl_event_handler.ts";
import * as telemetry from "../../telemetry_log.ts";

export class KuzuWasmClientImpl implements KuzuWasmClient {
  private db?: any;
  private conn?: any;
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private extendedRegistry = new ExtendedTemplateRegistry();
  private clientId = `wasm_${crypto.randomUUID()}`;
  private stateCache = new StateCache();
  private schemaManager: SchemaManager;

  constructor() {
    this.schemaManager = new SchemaManager(this.clientId);
  }

  async initialize(): Promise<void> {
    // Use sync version for Deno which doesn't support classic workers
    // TODO: ブラウザ環境では異なるインポート方法が必要になる可能性がある
    // 例: import("kuzu-wasm") for browser with worker support
    const kuzuModule = await import("kuzu-wasm/sync");
    const kuzu = kuzuModule.default || kuzuModule;
    
    // Initialize the WASM module
    await kuzu.init();
    
    // Database と Connection を作成
    this.db = new kuzu.Database(':memory:');
    this.conn = new kuzu.Connection(this.db);
    
    // Create schema
    await this.createSchema();
  }
  
  // Worker pathを取得するための拡張ポイント
  // TODO: ブラウザ環境でのWorker使用時には、このメソッドを実装して
  // 適切なWorkerスクリプトのパスを返す必要がある
  private getWorkerPath?(): string;

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
    telemetry.info("Replaying events from snapshot", { count: snapshot.events.length });
    for (const event of snapshot.events) {
      await this.applyEvent(event);
      this.events.push(event);
    }
  }

  async executeTemplate(template: string, params: Record<string, any>): Promise<TemplateEvent> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }
    
    // Check if this is a DDL template
    if (this.extendedRegistry.isDDLTemplate(template)) {
      // Create DDL event
      const ddlEvent = this.schemaManager.createDDLEvent(
        template as DDLOperationType,
        params
      );
      
      // Apply DDL event
      await this.applyEvent(ddlEvent);
      
      // Store event
      this.events.push(ddlEvent);
      
      return ddlEvent;
    }
    
    // For DML templates, use extended registry for validation
    const metadata = this.extendedRegistry.getTemplateMetadata(template);
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
    
    // Invalidate cache after applying new event
    this.stateCache.invalidateOnEvent(event);
    
    return event;
  }

  async getLocalState(): Promise<LocalState> {
    if (!this.conn) {
      return { users: [], posts: [], follows: [] };
    }
    
    // Check cache first for O(1) access
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
      
      // Cache the computed state
      this.stateCache.setCachedState(state);
      
      return state;
    } catch (error) {
      console.error("Error getting local state:", error);
      return { users: [], posts: [], follows: [] };
    }
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  // Public method to execute raw queries (for transaction support)
  async executeQuery(cypher: string, params?: Record<string, any>): Promise<any> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }
    return await this.conn.query(cypher, params);
  }

  // Query counter value
  async queryCounter(counterId: string): Promise<number> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }
    
    const result = await this.conn.query(`
      MATCH (c:Counter {id: $counterId})
      RETURN c.value as value
    `, { counterId });
    
    const table = result.getAll();
    if (table.length > 0 && table[0][0] !== null) {
      return table[0][0];
    }
    return 0; // Default if counter doesn't exist
  }

  // Schema query methods

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
      
      telemetry.info("Default database schema created");
    } else {
      telemetry.info("Schema already exists", {
        nodeTables: Object.keys(schemaState.nodeTables).length,
        edgeTables: Object.keys(schemaState.edgeTables).length
      });
    }
  }

  async applyEvent(event: TemplateEvent | DDLTemplateEvent): Promise<void> {
    if (!this.conn) {
      throw new Error("Client not initialized");
    }

    // Check if it's a DDL event
    if (isDDLEvent(event)) {
      try {
        await this.schemaManager.applyDDLEvent(
          event,
          (query: string) => this.conn.query(query)
        );
        // Notify handlers
        this.remoteEventHandlers.forEach(handler => handler(event));
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
      `,
      QUERY_COUNTER: `
        MATCH (c:Counter {id: $counterId})
        RETURN c.value as value
      `
    };
    
    const query = templates[event.template];
    if (query) {
      try {
        // Validate parameters using extended registry
        const metadata = this.extendedRegistry.getTemplateMetadata(event.template);
        const sanitizedParams = validateParams(event.params, metadata);
        
        // Log DML query execution with telemetry
        telemetry.info("Executing DML query", {
          template: event.template,
          eventId: event.id,
          query: query.trim(),
          params: sanitizedParams,
          timestamp: event.timestamp
        });
        
        const result = await this.conn.query(query, sanitizedParams);
        
        // Log successful execution
        telemetry.info("DML query executed successfully", {
          template: event.template,
          eventId: event.id
        });
        
        // Special handling for QUERY_COUNTER
        if (event.template === "QUERY_COUNTER") {
          // For query events, we need to return the result somehow
          // We'll store it in the event params for now
          const table = result.getAll();
          if (table.length > 0) {
            event.params._result = table[0][0]; // The value
          } else {
            event.params._result = 0; // Default if counter doesn't exist
          }
        } else {
          // Invalidate cache since state has changed (not for queries)
          this.stateCache.invalidateOnEvent(event);
        }
        
        // Notify handlers
        this.remoteEventHandlers.forEach(handler => handler(event));
      } catch (error) {
        // Log DML query error with telemetry
        telemetry.error("DML query execution failed", {
          template: event.template,
          eventId: event.id,
          query: query.trim(),
          params: event.params,
          error: error instanceof Error ? error.message : String(error)
        });
        console.error(`Failed to apply event ${event.id}:`, error);
        // Continue processing other events
      }
    } else {
      // Log unknown template warning
      telemetry.warn("Unknown DML template", {
        template: event.template,
        eventId: event.id
      });
    }
  }
}