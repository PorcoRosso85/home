/**
 * Schema Manager for Distributed KuzuDB
 * 分散KuzuDBのためのスキーママネージャー
 * 
 * 責務:
 * - スキーマバージョン管理
 * - DDL操作の追跡と適用
 * - クライアント間のスキーマ同期
 * - 現在のスキーマ状態の照会
 * - BrowserKuzuClientとの統合
 */

import { 
  DDLTemplateEvent, 
  DDLOperationType,
  SchemaVersion,
  SchemaState,
  NodeTableSchema,
  EdgeTableSchema,
  IndexSchema,
  isDDLEvent,
  isSchemaModifyingOperation 
} from "../event_sourcing/ddl_types.ts";
import { DDLEventHandler } from "../event_sourcing/ddl_event_handler.ts";
import { TemplateEvent } from "../event_sourcing/types.ts";
import { VectorClock } from "../distributed/vector_clock.ts";

/**
 * Schema synchronization state
 * スキーマ同期状態
 */
export interface SchemaSyncState {
  /** Current schema version */
  version: number;
  /** Vector clock for distributed consensus */
  vectorClock: VectorClock;
  /** Pending DDL operations */
  pendingDDLs: DDLTemplateEvent[];
  /** Conflicting DDL operations */
  conflicts: SchemaConflict[];
}

/**
 * Schema conflict representation
 * スキーマ競合の表現
 */
export interface SchemaConflict {
  /** Conflict ID */
  id: string;
  /** Conflicting DDL events */
  events: DDLTemplateEvent[];
  /** Conflict type */
  type: "CONCURRENT_MODIFICATION" | "DEPENDENCY_MISSING" | "VERSION_MISMATCH";
  /** Resolution strategy */
  resolution?: "APPLY_FIRST" | "APPLY_LAST" | "MANUAL" | "MERGE";
}

/**
 * Schema Manager class
 * スキーママネージャークラス
 */
export class SchemaManager {
  private currentVersion: SchemaVersion;
  private ddlHandler: DDLEventHandler;
  private appliedDDLs: Map<string, DDLTemplateEvent> = new Map();
  private pendingDDLs: Map<string, DDLTemplateEvent> = new Map();
  private schemaHistory: SchemaVersion[] = [];
  private vectorClock: VectorClock;
  private clientId: string;
  private conflicts: Map<string, SchemaConflict> = new Map();

  constructor(clientId: string) {
    this.clientId = clientId;
    this.ddlHandler = new DDLEventHandler();
    this.vectorClock = new VectorClock(clientId);
    
    // Initialize with empty schema
    this.currentVersion = {
      version: 0,
      timestamp: Date.now(),
      appliedEvents: [],
      schema: {
        nodeTables: {},
        edgeTables: {},
        indexes: {}
      }
    };
  }

  /**
   * Initialize schema from a snapshot
   * スナップショットからスキーマを初期化
   */
  async initializeFromSnapshot(
    events: TemplateEvent[],
    executeQuery: (query: string) => Promise<any>
  ): Promise<void> {
    // Reset state
    this.reset();
    
    // Filter and apply DDL events
    const ddlEvents = events.filter(isDDLEvent);
    
    for (const event of ddlEvents) {
      try {
        await this.applyDDLEvent(event, executeQuery);
      } catch (error) {
        console.error(`Failed to apply DDL event ${event.id} during initialization:`, error);
        // Continue with other events
      }
    }
  }

  /**
   * Create a new DDL event
   * 新しいDDLイベントを作成
   */
  createDDLEvent(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): DDLTemplateEvent {
    // Get dependencies based on current schema state
    const dependencies = this.calculateDependencies(ddlType, params);
    
    // Create DDL event
    const event = this.ddlHandler.createDDLEvent(ddlType, params, dependencies);
    
    // Update vector clock
    this.vectorClock.increment();
    
    return event;
  }

  /**
   * Apply a DDL event
   * DDLイベントを適用
   */
  async applyDDLEvent(
    event: DDLTemplateEvent,
    executeQuery: (query: string) => Promise<any>
  ): Promise<void> {
    // Check if already applied
    if (this.appliedDDLs.has(event.id)) {
      console.warn(`DDL event ${event.id} already applied`);
      return;
    }
    
    // Check dependencies
    const missingDeps = this.checkDependencies(event);
    if (missingDeps.length > 0) {
      // Add to pending queue
      this.pendingDDLs.set(event.id, event);
      throw new Error(`Missing dependencies: ${missingDeps.join(", ")}`);
    }
    
    try {
      // Apply the DDL
      await this.ddlHandler.applyDDLEvent(event, executeQuery);
      
      // Update schema state
      this.updateSchemaState(event);
      
      // Record application
      this.appliedDDLs.set(event.id, event);
      
      // Update vector clock if from remote
      if (event.clientId && event.clientId !== this.clientId) {
        this.vectorClock.update(event.clientId, event.timestamp);
      }
      
      // Check if any pending DDLs can now be applied
      await this.processPendingDDLs(executeQuery);
      
    } catch (error) {
      // Check if it's a conflict
      if (this.isSchemaConflict(error)) {
        this.handleSchemaConflict(event, error);
      }
      throw error;
    }
  }

  /**
   * Get current schema state
   * 現在のスキーマ状態を取得
   */
  getCurrentSchema(): SchemaState {
    return { ...this.currentVersion.schema };
  }

  /**
   * Get schema version
   * スキーマバージョンを取得
   */
  getSchemaVersion(): number {
    return this.currentVersion.version;
  }

  /**
   * Get schema synchronization state
   * スキーマ同期状態を取得
   */
  getSyncState(): SchemaSyncState {
    return {
      version: this.currentVersion.version,
      vectorClock: this.vectorClock.copy(),
      pendingDDLs: Array.from(this.pendingDDLs.values()),
      conflicts: Array.from(this.conflicts.values())
    };
  }

  /**
   * Query table existence
   * テーブルの存在を照会
   */
  hasTable(tableName: string): boolean {
    const schema = this.currentVersion.schema;
    return tableName in schema.nodeTables || tableName in schema.edgeTables;
  }

  /**
   * Query column existence
   * カラムの存在を照会
   */
  hasColumn(tableName: string, columnName: string): boolean {
    const schema = this.currentVersion.schema;
    
    const nodeTable = schema.nodeTables[tableName];
    if (nodeTable) {
      return columnName in nodeTable.columns;
    }
    
    const edgeTable = schema.edgeTables[tableName];
    if (edgeTable) {
      return columnName in edgeTable.columns;
    }
    
    return false;
  }

  /**
   * Get table schema
   * テーブルスキーマを取得
   */
  getTableSchema(tableName: string): NodeTableSchema | EdgeTableSchema | undefined {
    const schema = this.currentVersion.schema;
    return schema.nodeTables[tableName] || schema.edgeTables[tableName];
  }

  /**
   * Get applied DDL events
   * 適用済みDDLイベントを取得
   */
  getAppliedDDLs(): DDLTemplateEvent[] {
    return Array.from(this.appliedDDLs.values());
  }

  /**
   * Get pending DDL events
   * 保留中のDDLイベントを取得
   */
  getPendingDDLs(): DDLTemplateEvent[] {
    return Array.from(this.pendingDDLs.values());
  }

  /**
   * Resolve schema conflict
   * スキーマ競合を解決
   */
  async resolveConflict(
    conflictId: string,
    resolution: "APPLY_FIRST" | "APPLY_LAST" | "MANUAL",
    executeQuery: (query: string) => Promise<any>
  ): Promise<void> {
    const conflict = this.conflicts.get(conflictId);
    if (!conflict) {
      throw new Error(`Conflict ${conflictId} not found`);
    }
    
    switch (resolution) {
      case "APPLY_FIRST":
        // Apply the first event and discard others
        await this.applyDDLEvent(conflict.events[0], executeQuery);
        break;
        
      case "APPLY_LAST":
        // Apply the last event and discard others
        await this.applyDDLEvent(
          conflict.events[conflict.events.length - 1], 
          executeQuery
        );
        break;
        
      case "MANUAL":
        // Manual resolution required - mark as resolved
        conflict.resolution = "MANUAL";
        break;
    }
    
    // Remove conflict
    this.conflicts.delete(conflictId);
  }

  /**
   * Get schema history
   * スキーマ履歴を取得
   */
  getSchemaHistory(): SchemaVersion[] {
    return [...this.schemaHistory];
  }

  /**
   * Validate DDL against current schema
   * 現在のスキーマに対してDDLを検証
   */
  validateDDL(event: DDLTemplateEvent): { valid: boolean; errors: string[] } {
    const errors: string[] = [];
    
    if (!event.payload) {
      errors.push("DDL event missing payload");
      return { valid: false, errors };
    }
    
    const { ddlType } = event.payload;
    const params = event.params;
    
    switch (ddlType) {
      case "CREATE_NODE_TABLE":
      case "CREATE_TABLE":
        if (this.hasTable(params.tableName)) {
          errors.push(`Table ${params.tableName} already exists`);
        }
        break;
        
      case "DROP_NODE_TABLE":
      case "DROP_TABLE":
        if (!this.hasTable(params.tableName)) {
          errors.push(`Table ${params.tableName} does not exist`);
        }
        break;
        
      case "ADD_COLUMN":
      case "ALTER_TABLE_ADD_COLUMN":
        if (!this.hasTable(params.tableName)) {
          errors.push(`Table ${params.tableName} does not exist`);
        } else if (this.hasColumn(params.tableName, params.columnName)) {
          errors.push(`Column ${params.columnName} already exists in table ${params.tableName}`);
        }
        break;
        
      case "DROP_COLUMN":
      case "ALTER_TABLE_DROP_COLUMN":
        if (!this.hasTable(params.tableName)) {
          errors.push(`Table ${params.tableName} does not exist`);
        } else if (!this.hasColumn(params.tableName, params.columnName)) {
          errors.push(`Column ${params.columnName} does not exist in table ${params.tableName}`);
        }
        break;
    }
    
    return { valid: errors.length === 0, errors };
  }

  // Private methods

  private calculateDependencies(
    ddlType: DDLOperationType,
    params: Record<string, any>
  ): string[] {
    const dependencies: string[] = [];
    
    // Add dependencies based on DDL type
    switch (ddlType) {
      case "CREATE_EDGE_TABLE":
        // Depends on source and target tables
        const fromTableDDL = this.findCreateTableDDL(params.fromTable);
        const toTableDDL = this.findCreateTableDDL(params.toTable);
        if (fromTableDDL) dependencies.push(fromTableDDL);
        if (toTableDDL) dependencies.push(toTableDDL);
        break;
        
      case "ADD_COLUMN":
      case "ALTER_TABLE_ADD_COLUMN":
      case "DROP_COLUMN":
      case "ALTER_TABLE_DROP_COLUMN":
      case "RENAME_COLUMN":
        // Depends on table creation
        const createTableDDL = this.findCreateTableDDL(params.tableName);
        if (createTableDDL) {
          dependencies.push(createTableDDL);
        } else {
          // If table doesn't exist, create a synthetic dependency
          // This will cause the DDL to be pending until the table is created
          dependencies.push(`CREATE_TABLE_${params.tableName}`);
        }
        break;
    }
    
    return dependencies;
  }

  private findCreateTableDDL(tableName: string): string | undefined {
    for (const [eventId, event] of this.appliedDDLs) {
      if (event.payload && 
          (event.payload.ddlType === "CREATE_NODE_TABLE" || 
           event.payload.ddlType === "CREATE_TABLE" ||
           event.payload.ddlType === "CREATE_EDGE_TABLE") &&
          event.params.tableName === tableName) {
        return eventId;
      }
    }
    return undefined;
  }

  private checkDependencies(event: DDLTemplateEvent): string[] {
    const missing: string[] = [];
    
    for (const depId of event.dependsOn) {
      if (!this.appliedDDLs.has(depId)) {
        missing.push(depId);
      }
    }
    
    return missing;
  }

  private async processPendingDDLs(
    executeQuery: (query: string) => Promise<any>
  ): Promise<void> {
    const processed = new Set<string>();
    
    for (const [eventId, event] of this.pendingDDLs) {
      // For ADD_COLUMN operations, check if the table now exists
      if (event.payload && 
          (event.payload.ddlType === "ADD_COLUMN" || 
           event.payload.ddlType === "ALTER_TABLE_ADD_COLUMN" ||
           event.payload.ddlType === "DROP_COLUMN" ||
           event.payload.ddlType === "ALTER_TABLE_DROP_COLUMN")) {
        const tableName = event.params.tableName;
        if (this.hasTable(tableName)) {
          // Table now exists, try to apply the DDL
          try {
            // Clear synthetic dependencies since table now exists
            const cleanedEvent = {
              ...event,
              dependsOn: event.dependsOn.filter(dep => !dep.startsWith('CREATE_TABLE_'))
            };
            // Apply DDL with cleaned dependencies
            await this.ddlHandler.applyDDLEvent(cleanedEvent, executeQuery);
            this.updateSchemaState(cleanedEvent);
            this.appliedDDLs.set(event.id, cleanedEvent);
            this.currentVersion.version++;
            this.currentVersion.timestamp = Date.now();
            this.currentVersion.appliedEvents.push(event.id);
            this.schemaHistory.push({ ...this.currentVersion });
            processed.add(eventId);
          } catch (error) {
            console.error(`Failed to process pending DDL ${eventId}:`, error);
          }
        }
      } else {
        // For other DDL types, check normal dependencies
        const missingDeps = this.checkDependencies(event);
        if (missingDeps.length === 0) {
          try {
            // Mark as processed first to avoid infinite recursion
            processed.add(eventId);
            // Remove from pending
            this.pendingDDLs.delete(eventId);
            // Apply without calling processPendingDDLs again
            await this.ddlHandler.applyDDLEvent(event, executeQuery);
            this.updateSchemaState(event);
            this.appliedDDLs.set(event.id, event);
            this.currentVersion.version++;
            this.currentVersion.timestamp = Date.now();
            this.currentVersion.appliedEvents.push(event.id);
            this.schemaHistory.push({ ...this.currentVersion });
          } catch (error) {
            console.error(`Failed to process pending DDL ${eventId}:`, error);
            // Re-add to pending if failed
            this.pendingDDLs.set(eventId, event);
            processed.delete(eventId);
          }
        }
      }
    }
    
    // Remove processed DDLs from pending
    for (const eventId of processed) {
      this.pendingDDLs.delete(eventId);
    }
  }

  private updateSchemaState(event: DDLTemplateEvent): void {
    if (!event.payload) return;
    
    const { ddlType } = event.payload;
    const params = event.params;
    const schema = this.currentVersion.schema;
    
    // Apply schema changes based on DDL type
    switch (ddlType) {
      case "CREATE_NODE_TABLE":
      case "CREATE_TABLE":
        schema.nodeTables[params.tableName] = {
          name: params.tableName,
          columns: this.createColumnsSchema(params.columns),
          primaryKey: params.primaryKey,
          comment: params.comment
        };
        break;
        
      case "CREATE_EDGE_TABLE":
        schema.edgeTables[params.tableName] = {
          name: params.tableName,
          fromTable: params.fromTable,
          toTable: params.toTable,
          columns: this.createColumnsSchema(params.columns || []),
          comment: params.comment
        };
        break;
        
      case "DROP_NODE_TABLE":
      case "DROP_TABLE":
        delete schema.nodeTables[params.tableName];
        delete schema.edgeTables[params.tableName];
        break;
        
      case "ADD_COLUMN":
      case "ALTER_TABLE_ADD_COLUMN":
        const table = schema.nodeTables[params.tableName] || 
                     schema.edgeTables[params.tableName];
        if (table) {
          table.columns[params.columnName] = {
            name: params.columnName,
            type: params.dataType,
            nullable: params.nullable ?? true,
            defaultValue: params.defaultValue,
            comment: params.comment
          };
        }
        break;
        
      case "DROP_COLUMN":
      case "ALTER_TABLE_DROP_COLUMN":
        const tableForDrop = schema.nodeTables[params.tableName] || 
                            schema.edgeTables[params.tableName];
        if (tableForDrop) {
          delete tableForDrop.columns[params.columnName];
        }
        break;
    }
    
    // Update version if schema was modified
    if (isSchemaModifyingOperation(ddlType)) {
      this.currentVersion = {
        version: this.currentVersion.version + 1,
        timestamp: Date.now(),
        appliedEvents: [...this.currentVersion.appliedEvents, event.id],
        schema: { ...schema }
      };
      
      // Add to history
      this.schemaHistory.push({ ...this.currentVersion });
    }
  }

  private createColumnsSchema(
    columns: Array<{ name: string; type: string; nullable?: boolean; defaultValue?: any }>
  ): Record<string, any> {
    const columnsSchema: Record<string, any> = {};
    
    for (const col of columns) {
      columnsSchema[col.name] = {
        name: col.name,
        type: col.type,
        nullable: col.nullable ?? true,
        defaultValue: col.defaultValue
      };
    }
    
    return columnsSchema;
  }

  private isSchemaConflict(error: any): boolean {
    // Check for common conflict indicators
    const errorMessage = error.message?.toLowerCase() || "";
    return errorMessage.includes("already exists") ||
           errorMessage.includes("does not exist") ||
           errorMessage.includes("conflict") ||
           errorMessage.includes("concurrent");
  }

  private handleSchemaConflict(event: DDLTemplateEvent, error: any): void {
    const conflictId = `conflict_${crypto.randomUUID()}`;
    
    // Find related events that might be conflicting
    const relatedEvents = this.findRelatedDDLs(event);
    
    const conflict: SchemaConflict = {
      id: conflictId,
      events: [event, ...relatedEvents],
      type: this.determineConflictType(event, error),
      resolution: undefined
    };
    
    this.conflicts.set(conflictId, conflict);
  }

  private findRelatedDDLs(event: DDLTemplateEvent): DDLTemplateEvent[] {
    const related: DDLTemplateEvent[] = [];
    const tableName = event.params.tableName;
    
    if (!tableName) return related;
    
    // Find DDLs that affect the same table
    for (const appliedEvent of this.appliedDDLs.values()) {
      if (appliedEvent.params.tableName === tableName && 
          appliedEvent.id !== event.id) {
        related.push(appliedEvent);
      }
    }
    
    return related;
  }

  private determineConflictType(
    event: DDLTemplateEvent,
    error: any
  ): SchemaConflict["type"] {
    const errorMessage = error.message?.toLowerCase() || "";
    
    if (errorMessage.includes("dependency")) {
      return "DEPENDENCY_MISSING";
    } else if (errorMessage.includes("version")) {
      return "VERSION_MISMATCH";
    } else {
      return "CONCURRENT_MODIFICATION";
    }
  }

  private reset(): void {
    this.appliedDDLs.clear();
    this.pendingDDLs.clear();
    this.conflicts.clear();
    this.schemaHistory = [];
    this.ddlHandler.reset();
    
    this.currentVersion = {
      version: 0,
      timestamp: Date.now(),
      appliedEvents: [],
      schema: {
        nodeTables: {},
        edgeTables: {},
        indexes: {}
      }
    };
  }
}

/**
 * Schema Manager Factory
 * スキーママネージャーファクトリー
 */
export function createSchemaManager(clientId: string): SchemaManager {
  return new SchemaManager(clientId);
}