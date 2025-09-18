/**
 * KuzuDB TypeScript Client - Native Deno Implementation
 * persistence/kuzu_tsパッケージを使用したネイティブ実装
 * 
 * ## Known Limitations
 * 
 * ### V8 Isolate Lifecycle Issues
 * - The persistence/kuzu_ts package experiences V8 isolate lifecycle issues on Deno exit
 * - The implementation works correctly during runtime but may crash on process termination
 * - This is a temporary implementation until a proper FFI-based solution is available
 * 
 * These limitations do not affect the correctness of operations during normal runtime.
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

// Import from persistence/kuzu_ts using Worker implementation
import { 
  createDatabase, 
  createConnection, 
  terminateWorker,
  type WorkerDatabase,
  type WorkerConnection
} from "@kuzu-ts/worker";

// Type definitions for kuzu_ts module
type KuzuQueryResult = {
  getAll(): Promise<unknown[][]>;
};

type DatabaseResult = WorkerDatabase | { type: string; message: string };
type ConnectionResult = WorkerConnection | { type: string; message: string };

function isError(result: any): result is { type: string; message: string } {
  return typeof result === "object" && "type" in result && "message" in result;
}

export class KuzuTsClientImpl implements KuzuWasmClient {
  private db?: WorkerDatabase; // Database instance
  private conn?: WorkerConnection; // Connection instance
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private extendedRegistry = new ExtendedTemplateRegistry();
  private clientId = `ts_${crypto.randomUUID()}`;
  private stateCache = new StateCache();
  private schemaManager: SchemaManager;
  private isInitialized = false;
  private isCleanedUp = false;

  constructor() {
    this.schemaManager = new SchemaManager(this.clientId);
  }

  async initialize(): Promise<void> {
    if (this.isInitialized) {
      telemetry.warn("Client already initialized", { clientId: this.clientId });
      return;
    }
    
    if (this.isCleanedUp) {
      throw new Error("Cannot initialize a cleaned up client. Create a new instance.");
    }
    
    telemetry.info("Initializing TypeScript KuzuDB client", {
      clientId: this.clientId
    });

    try {
      // Create in-memory database
      const dbResult = await createDatabase(":memory:", { bufferPoolSize: 1024 * 1024 * 100 });
      
      if (isError(dbResult)) {
        throw new Error(`Failed to create database: ${dbResult.message}`);
      }
      
      this.db = dbResult;
      
      // Create connection
      const connResult = await createConnection(this.db!);
      
      if (isError(connResult)) {
        // Cleanup database on connection failure
        await this.cleanup();
        throw new Error(`Failed to create connection: ${connResult.message}`);
      }
      
      this.conn = connResult;
      
      // Create schema
      await this.createSchema();
      
      telemetry.info("TypeScript KuzuDB client initialized successfully");
      this.isInitialized = true;
    } catch (error) {
      telemetry.error("Failed to initialize TypeScript KuzuDB client", {
        error: error instanceof Error ? error.message : String(error),
        clientId: this.clientId
      });
      // Ensure cleanup on any initialization failure
      await this.cleanup();
      throw error;
    }
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
    try {
      await this.initialize();
      
      // Clear existing state
      this.events = [];
      this.stateCache.clear();
      
      // Initialize schema manager from snapshot
      await this.schemaManager.initializeFromSnapshot(
        snapshot.events,
        (query: string) => this.conn!.query(query)
      );
      
      // Replay all events from snapshot
      telemetry.info("Replaying events from snapshot", { count: snapshot.events.length });
      for (const event of snapshot.events) {
        await this.applyEvent(event);
        this.events.push(event);
      }
    } catch (error) {
      telemetry.error("Failed to initialize from snapshot", {
        error: error instanceof Error ? error.message : String(error),
        clientId: this.clientId
      });
      // Ensure cleanup on snapshot initialization failure
      await this.cleanup();
      throw error;
    }
  }

  async executeTemplate(template: string, params: Record<string, unknown>): Promise<TemplateEvent> {
    if (!this.isInitialized || this.isCleanedUp) {
      throw new Error("Client not initialized or already cleaned up");
    }
    
    if (!this.conn) {
      throw new Error("Connection not available");
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
    if (!this.isInitialized || this.isCleanedUp) {
      return { users: [], posts: [], follows: [] };
    }
    
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
      const rows = await userResult.getAll();
      const users = rows.map((row: any[]) => ({
        id: row[0],
        name: row[1],
        email: row[2]
      }));
      
      // Get posts
      const postResult = await this.conn.query(`
        MATCH (p:Post)
        RETURN p.id as id, p.content as content, p.authorId as authorId
        ORDER BY p.id
      `);
      const postRows = await postResult.getAll();
      const posts = postRows.map((row: any[]) => ({
        id: row[0],
        content: row[1],
        authorId: row[2]
      }));
      
      // Get follows
      const followResult = await this.conn.query(`
        MATCH (follower:User)-[:FOLLOWS]->(target:User)
        RETURN follower.id as followerId, target.id as targetId
      `);
      const followRows = await followResult.getAll();
      const follows = followRows.map((row: any[]) => ({
        followerId: row[0],
        targetId: row[1]
      }));
      
      const state = { users, posts, follows };
      
      // Cache the computed state
      this.stateCache.setCachedState(state);
      
      return state;
    } catch (error) {
      telemetry.error("Error getting local state", {
        error: error instanceof Error ? error.message : String(error),
        clientId: this.clientId
      });
      return { users: [], posts: [], follows: [] };
    }
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  async executeQuery(cypher: string, params?: Record<string, unknown>): Promise<unknown> {
    if (!this.isInitialized || this.isCleanedUp) {
      throw new Error("Client not initialized or already cleaned up");
    }
    
    if (!this.conn) {
      throw new Error("Connection not available");
    }
    // Worker implementation doesn't support parameters, need to inline them
    if (params) {
      let query = cypher;
      for (const [key, value] of Object.entries(params)) {
        const placeholder = `$${key}`;
        const replacement = typeof value === 'string' ? `'${value}'` : String(value);
        query = query.replace(new RegExp(`\\${placeholder}\\b`, 'g'), replacement);
      }
      return await this.conn.query(query);
    }
    return await this.conn.query(cypher);
  }

  async applyEvent(event: TemplateEvent | DDLTemplateEvent): Promise<void> {
    if (!this.isInitialized || this.isCleanedUp) {
      throw new Error("Client not initialized or already cleaned up");
    }
    
    if (!this.conn) {
      throw new Error("Connection not available");
    }

    // Check if it's a DDL event
    if (isDDLEvent(event)) {
      try {
        await this.schemaManager.applyDDLEvent(
          event,
          (query: string) => this.conn!.query(query)
        );
        // Notify handlers
        this.remoteEventHandlers.forEach(handler => handler(event));
      } catch (error) {
        telemetry.error(`Failed to apply DDL event ${event.id}`, {
          error: error instanceof Error ? error.message : String(error),
          clientId: this.clientId
        });
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
          timestamp: event.timestamp,
          clientId: this.clientId
        });
        
        // Worker implementation doesn't support parameters, need to inline them
        let inlinedQuery = query;
        for (const [key, value] of Object.entries(sanitizedParams)) {
          const placeholder = `$${key}`;
          const replacement = typeof value === 'string' ? `'${value}'` : String(value);
          inlinedQuery = inlinedQuery.replace(new RegExp(`\\${placeholder}\\b`, 'g'), replacement);
        }
        const result = await this.conn.query(inlinedQuery);
        
        // Log successful execution
        telemetry.info("DML query executed successfully", {
          template: event.template,
          eventId: event.id,
          clientId: this.clientId
        });
        
        // Special handling for QUERY_COUNTER
        if (event.template === "QUERY_COUNTER") {
          const rows = await result.getAll();
          if (rows.length > 0) {
            event.params._result = rows[0][0]; // The value
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
          error: error instanceof Error ? error.message : String(error),
          clientId: this.clientId
        });
        telemetry.error(`Failed to apply event ${event.id}`, {
          error: error instanceof Error ? error.message : String(error)
        });
        // Continue processing other events
      }
    } else {
      // Log unknown template warning
      telemetry.warn("Unknown DML template", {
        template: event.template,
        eventId: event.id,
        clientId: this.clientId
      });
    }
  }

  private async createSchema(): Promise<void> {
    // Check current schema state
    const schemaState = this.schemaManager.getCurrentSchema();
    
    // Create default schema if no tables exist
    if (Object.keys(schemaState.nodeTables).length === 0) {
      // Create User node table
      if (!this.schemaManager.hasTable("User")) {
        await this.conn!.query(`
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
        await this.conn!.query(`
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
        await this.conn!.query(`
          CREATE REL TABLE IF NOT EXISTS FOLLOWS(FROM User TO User)
        `);
      }
      
      // Create Counter node table
      if (!this.schemaManager.hasTable("Counter")) {
        await this.conn!.query(`
          CREATE NODE TABLE IF NOT EXISTS Counter(
            id STRING,
            value INT64,
            PRIMARY KEY(id)
          )
        `);
      }
      
      telemetry.info("Default database schema created", {
        clientId: this.clientId
      });
    } else {
      telemetry.info("Schema already exists", {
        nodeTables: Object.keys(schemaState.nodeTables).length,
        edgeTables: Object.keys(schemaState.edgeTables).length,
        clientId: this.clientId
      });
    }
  }

  // Query counter value
  async queryCounter(counterId: string): Promise<number> {
    if (!this.isInitialized || this.isCleanedUp) {
      throw new Error("Client not initialized or already cleaned up");
    }
    
    if (!this.conn) {
      throw new Error("Connection not available");
    }
    
    const result = await this.conn.query(`
      MATCH (c:Counter {id: '${counterId}'})
      RETURN c.value as value
    `);
    
    const rows = await result.getAll();
    if (rows.length > 0 && rows[0][0] !== null && rows[0][0] !== undefined) {
      return rows[0][0] as number;
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
      (query: string) => this.conn!.query(query)
    );
  }

  // DDL Event Creation
  createDDLEvent(
    ddlType: DDLOperationType,
    params: Record<string, unknown>
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

  getTemplateMetadata(template: string): unknown {
    return this.extendedRegistry.getTemplateMetadata(template);
  }

  // Check if client needs cleanup
  needsCleanup(): boolean {
    return this.isInitialized && !this.isCleanedUp;
  }

  // Ensure cleanup is called (for use in finally blocks)
  async ensureCleanup(): Promise<void> {
    if (this.needsCleanup()) {
      await this.cleanup();
    }
  }

  // Cleanup method with proper error handling
  async cleanup(): Promise<void> {
    if (this.isCleanedUp) {
      telemetry.warn("Client already cleaned up", { clientId: this.clientId });
      return;
    }
    
    telemetry.info("Starting client cleanup", {
      clientId: this.clientId,
      hasDb: !!this.db,
      hasConn: !!this.conn,
      isInitialized: this.isInitialized
    });
    
    this.isCleanedUp = true;
    const errors: Error[] = [];
    
    // Close connection first (if exists)
    if (this.conn) {
      try {
        // Connection doesn't have explicit close in Worker implementation
        this.conn = undefined;
      } catch (error) {
        errors.push(new Error(`Failed to close connection: ${error}`));
      }
    }
    
    // Close database
    if (this.db) {
      try {
        await this.db.close();
        this.db = undefined;
      } catch (error) {
        errors.push(new Error(`Failed to close database: ${error}`));
      }
    }
    
    // Terminate worker
    try {
      await terminateWorker();
    } catch (error) {
      errors.push(new Error(`Failed to terminate worker: ${error}`));
    }
    
    // Clear internal state
    this.events = [];
    this.remoteEventHandlers = [];
    this.stateCache.clear();
    
    if (errors.length > 0) {
      telemetry.error("Errors during cleanup", {
        clientId: this.clientId,
        errors: errors.map(e => e.message)
      });
      // Still throw the first error after attempting all cleanup
      throw errors[0];
    }
    
    telemetry.info("Client cleanup completed successfully", {
      clientId: this.clientId
    });
    
    this.isInitialized = false;
  }
}