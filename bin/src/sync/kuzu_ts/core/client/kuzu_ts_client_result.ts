/**
 * KuzuDB TypeScript Client - Native Deno Implementation with Result Pattern
 * persistence/kuzu_tsパッケージを使用したネイティブ実装（Result型パターン使用）
 * 
 * FIXME: Current limitations:
 * 1. persistence/kuzu_ts has V8 isolate lifecycle issues on Deno exit
 * 2. Works correctly but crashes on process termination
 * 3. This is a temporary implementation until FFI solution is ready
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
import { Result, success, failure, isSuccess } from "../result.ts";

// Type definitions for kuzu_ts module
type KuzuDatabase = {
  close(): void;
};

type KuzuConnection = {
  query(statement: string, params?: Record<string, unknown>): Promise<KuzuQueryResult>;
};

type KuzuQueryResult = {
  getAll(): unknown[][];
  getAllObjects(): Record<string, unknown>[];
};

type DatabaseResult = KuzuDatabase | { type: string; message: string };
type ConnectionResult = KuzuConnection | { type: string; message: string };

// Error types
type KuzuError = {
  type: "NOT_INITIALIZED" | "DATABASE_ERROR" | "CONNECTION_ERROR" | "QUERY_ERROR" | "VALIDATION_ERROR";
  message: string;
  details?: unknown;
};

// Import from persistence/kuzu_ts using import map
async function importKuzuTs(): Promise<Result<{ createDatabase: unknown; createConnection: unknown }, KuzuError>> {
  try {
    const module = await import("@kuzu-ts/mod.ts");
    return success(module);
  } catch (error) {
    return failure({
      type: "DATABASE_ERROR",
      message: "Failed to import kuzu_ts module",
      details: error
    });
  }
}

function isError(result: DatabaseResult | ConnectionResult): result is { type: string; message: string } {
  return typeof result === "object" && "type" in result && "message" in result;
}

export class KuzuTsClientImplResult implements KuzuWasmClient {
  private db?: KuzuDatabase;
  private conn?: KuzuConnection;
  private events: TemplateEvent[] = [];
  private remoteEventHandlers: Array<(event: TemplateEvent) => void> = [];
  private registry = new TemplateRegistry();
  private extendedRegistry = new ExtendedTemplateRegistry();
  private clientId = `ts_${crypto.randomUUID()}`;
  private stateCache = new StateCache();
  private schemaManager: SchemaManager;
  private kuzuModule?: { createDatabase: unknown; createConnection: unknown };

  constructor() {
    this.schemaManager = new SchemaManager(this.clientId);
  }

  async initialize(): Promise<void> {
    const result = await this.initializeWithResult();
    if (!result.ok) {
      // KuzuWasmClient interface expects void return, so we log the error
      telemetry.error("Failed to initialize client", result.error);
    }
  }

  async initializeWithResult(): Promise<Result<void, KuzuError>> {
    telemetry.info("Initializing TypeScript KuzuDB client", {
      clientId: this.clientId
    });

    // Import kuzu_ts module
    const moduleResult = await importKuzuTs();
    if (!isSuccess(moduleResult)) {
      return failure(moduleResult.error);
    }
    
    this.kuzuModule = moduleResult.data;
    
    // Create in-memory database
    const createDatabase = this.kuzuModule.createDatabase as (path: string, options: unknown) => DatabaseResult;
    const dbResult = createDatabase(":memory:", { testUnique: true });
    
    if (isError(dbResult)) {
      return failure({
        type: "DATABASE_ERROR",
        message: `Failed to create database: ${dbResult.message}`
      });
    }
    
    this.db = dbResult;
    
    // Create connection
    const createConnection = this.kuzuModule.createConnection as (db: KuzuDatabase) => ConnectionResult;
    const connResult = createConnection(this.db);
    
    if (isError(connResult)) {
      return failure({
        type: "CONNECTION_ERROR",
        message: `Failed to create connection: ${connResult.message}`
      });
    }
    
    this.conn = connResult;
    
    // Create schema
    const schemaResult = await this.createSchemaWithResult();
    if (!isSuccess(schemaResult)) {
      return failure(schemaResult.error);
    }
    
    telemetry.info("TypeScript KuzuDB client initialized successfully");
    return success(undefined);
  }

  async initializeFromSnapshot(snapshot: EventSnapshot): Promise<void> {
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
  }

  async executeTemplate(template: string, params: Record<string, unknown>): Promise<TemplateEvent> {
    const result = await this.executeTemplateWithResult(template, params);
    if (!result.ok) {
      // For compatibility with existing interface
      telemetry.error("Template execution failed", result.error);
      // Return a failed event for compatibility
      return createTemplateEvent("ERROR", { error: result.error }, this.clientId);
    }
    return result.data;
  }

  async executeTemplateWithResult(template: string, params: Record<string, unknown>): Promise<Result<TemplateEvent, KuzuError>> {
    if (!this.conn) {
      return failure({
        type: "NOT_INITIALIZED",
        message: "Client not initialized"
      });
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
      
      return success(ddlEvent);
    }
    
    // For DML templates, use extended registry for validation
    const metadata = this.extendedRegistry.getTemplateMetadata(template);
    const sanitizedParams = validateParams(params, metadata);
    
    // Check for injection attempts
    for (const value of Object.values(sanitizedParams)) {
      if (typeof value === 'string' && 
          (value.includes("DROP") || value.includes("DELETE") || value.includes("--"))) {
        return failure({
          type: "VALIDATION_ERROR",
          message: "Invalid parameter: potential injection attempt"
        });
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
    
    return success(event);
  }

  async getLocalState(): Promise<LocalState> {
    const result = await this.getLocalStateWithResult();
    if (!result.ok) {
      return { users: [], posts: [], follows: [] };
    }
    return result.data;
  }

  async getLocalStateWithResult(): Promise<Result<LocalState, KuzuError>> {
    if (!this.conn) {
      return success({ users: [], posts: [], follows: [] });
    }
    
    // Check cache first for O(1) access
    const cachedState = this.stateCache.getCachedState();
    if (cachedState) {
      return success(cachedState);
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
      
      const state = { users, posts, follows } as LocalState;
      
      // Cache the computed state
      this.stateCache.setCachedState(state);
      
      return success(state);
    } catch (error) {
      return failure({
        type: "QUERY_ERROR",
        message: "Error getting local state",
        details: error
      });
    }
  }

  onRemoteEvent(handler: (event: TemplateEvent) => void): void {
    this.remoteEventHandlers.push(handler);
  }

  async executeQuery(cypher: string, params?: Record<string, unknown>): Promise<unknown> {
    const result = await this.executeQueryWithResult(cypher, params);
    if (!result.ok) {
      telemetry.error("Query execution failed", result.error);
      return null;
    }
    return result.data;
  }

  async executeQueryWithResult(cypher: string, params?: Record<string, unknown>): Promise<Result<unknown, KuzuError>> {
    if (!this.conn) {
      return failure({
        type: "NOT_INITIALIZED",
        message: "Client not initialized"
      });
    }
    
    try {
      const result = await this.conn.query(cypher, params);
      return success(result);
    } catch (error) {
      return failure({
        type: "QUERY_ERROR",
        message: "Query execution failed",
        details: error
      });
    }
  }

  async applyEvent(event: TemplateEvent | DDLTemplateEvent): Promise<void> {
    const result = await this.applyEventWithResult(event);
    if (!result.ok) {
      telemetry.error("Failed to apply event", result.error);
    }
  }

  async applyEventWithResult(event: TemplateEvent | DDLTemplateEvent): Promise<Result<void, KuzuError>> {
    if (!this.conn) {
      return failure({
        type: "NOT_INITIALIZED",
        message: "Client not initialized"
      });
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
        return success(undefined);
      } catch (error) {
        return failure({
          type: "QUERY_ERROR",
          message: `Failed to apply DDL event ${event.id}`,
          details: error
        });
      }
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
        
        const result = await this.conn.query(query, sanitizedParams);
        
        // Log successful execution
        telemetry.info("DML query executed successfully", {
          template: event.template,
          eventId: event.id,
          clientId: this.clientId
        });
        
        // Special handling for QUERY_COUNTER
        if (event.template === "QUERY_COUNTER") {
          const rows = result.getAll();
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
        return success(undefined);
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
        return failure({
          type: "QUERY_ERROR",
          message: `Failed to apply event ${event.id}`,
          details: error
        });
      }
    } else {
      // Log unknown template warning
      telemetry.warn("Unknown DML template", {
        template: event.template,
        eventId: event.id,
        clientId: this.clientId
      });
      return success(undefined); // Continue processing
    }
  }

  private async createSchemaWithResult(): Promise<Result<void, KuzuError>> {
    if (!this.conn) {
      return failure({
        type: "NOT_INITIALIZED",
        message: "Connection not initialized"
      });
    }
    
    try {
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
      
      return success(undefined);
    } catch (error) {
      return failure({
        type: "QUERY_ERROR",
        message: "Failed to create schema",
        details: error
      });
    }
  }

  private async createSchema(): Promise<void> {
    const result = await this.createSchemaWithResult();
    if (!result.ok) {
      telemetry.error("Schema creation failed", result.error);
    }
  }

  // Query counter value
  async queryCounter(counterId: string): Promise<number> {
    const result = await this.queryCounterWithResult(counterId);
    if (!result.ok) {
      return 0;
    }
    return result.data;
  }

  async queryCounterWithResult(counterId: string): Promise<Result<number, KuzuError>> {
    if (!this.conn) {
      return failure({
        type: "NOT_INITIALIZED",
        message: "Client not initialized"
      });
    }
    
    try {
      const result = await this.conn.query(`
        MATCH (c:Counter {id: $counterId})
        RETURN c.value as value
      `, { counterId });
      
      const rows = result.getAll();
      if (rows.length > 0 && rows[0][0] !== null) {
        return success(rows[0][0] as number);
      }
      return success(0); // Default if counter doesn't exist
    } catch (error) {
      return failure({
        type: "QUERY_ERROR",
        message: "Failed to query counter",
        details: error
      });
    }
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
}