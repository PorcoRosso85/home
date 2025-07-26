/**
 * DDL Types for Event Sourcing
 * DDL操作のためのイベントソーシング型定義
 */

import { TemplateEvent, EventImpact } from "./types.ts";

// ========== Extended Event Types ==========

/**
 * Extended TemplateEvent interface with DDL support
 * DDL操作をサポートする拡張TemplateEventインターフェース
 */
export interface DDLTemplateEvent extends TemplateEvent {
  /** Event type to distinguish DDL from DML operations */
  type: "DDL" | "DML";
  /** Dependencies for causal ordering */
  dependsOn: string[];
  /** DDL-specific payload */
  payload?: DDLPayload;
}

/**
 * DDL payload structure
 * DDL操作のペイロード構造
 */
export interface DDLPayload {
  /** Type of DDL operation */
  ddlType: DDLOperationType;
  /** The actual DDL query */
  query: string;
  /** Optional metadata for the operation */
  metadata?: DDLMetadata;
}

/**
 * DDL operation types
 * DDL操作のタイプ
 */
export type DDLOperationType =
  // Node table operations
  | "CREATE_NODE_TABLE"
  | "CREATE_TABLE"  // Alias for CREATE_NODE_TABLE
  | "DROP_NODE_TABLE"
  | "DROP_TABLE"    // Alias for DROP_NODE_TABLE
  
  // Edge table operations
  | "CREATE_EDGE_TABLE"
  | "DROP_EDGE_TABLE"
  
  // Column operations
  | "ADD_COLUMN"
  | "ALTER_TABLE_ADD_COLUMN"  // More explicit alias
  | "DROP_COLUMN"
  | "ALTER_TABLE_DROP_COLUMN" // More explicit alias
  | "RENAME_COLUMN"
  | "ALTER_COLUMN_TYPE"
  
  // Table modifications
  | "RENAME_TABLE"
  | "COMMENT_ON_TABLE"
  | "COMMENT_ON_COLUMN"
  
  // Index operations
  | "CREATE_INDEX"
  | "DROP_INDEX"
  
  // Constraint operations
  | "ADD_CONSTRAINT"
  | "DROP_CONSTRAINT";

/**
 * DDL metadata for additional operation context
 * DDL操作の追加コンテキストメタデータ
 */
export interface DDLMetadata {
  /** Whether to use IF NOT EXISTS clause */
  ifNotExists?: boolean;
  /** Whether to use IF EXISTS clause */
  ifExists?: boolean;
  /** Default value for column operations */
  defaultValue?: any;
  /** Comment text for COMMENT operations */
  comment?: string;
  /** Whether operation should cascade */
  cascade?: boolean;
}

// ========== Schema Version Types ==========

/**
 * Schema version tracking
 * スキーマバージョンの追跡
 */
export interface SchemaVersion {
  /** Version number */
  version: number;
  /** Timestamp of the version */
  timestamp: number;
  /** List of DDL events applied in this version */
  appliedEvents: string[];
  /** Current schema state */
  schema: SchemaState;
}

/**
 * Schema state representation
 * スキーマ状態の表現
 */
export interface SchemaState {
  /** Node tables in the schema */
  nodeTables: Record<string, NodeTableSchema>;
  /** Edge tables in the schema */
  edgeTables: Record<string, EdgeTableSchema>;
  /** Indexes in the schema */
  indexes: Record<string, IndexSchema>;
}

/**
 * Node table schema
 * ノードテーブルスキーマ
 */
export interface NodeTableSchema {
  /** Table name */
  name: string;
  /** Columns in the table */
  columns: Record<string, ColumnSchema>;
  /** Primary key column(s) */
  primaryKey: string[];
  /** Table comment */
  comment?: string;
}

/**
 * Edge table schema
 * エッジテーブルスキーマ
 */
export interface EdgeTableSchema {
  /** Table name */
  name: string;
  /** Source node table */
  fromTable: string;
  /** Target node table */
  toTable: string;
  /** Columns in the table */
  columns: Record<string, ColumnSchema>;
  /** Table comment */
  comment?: string;
}

/**
 * Column schema
 * カラムスキーマ
 */
export interface ColumnSchema {
  /** Column name */
  name: string;
  /** Data type */
  type: KuzuDataType;
  /** Whether column is nullable */
  nullable: boolean;
  /** Default value */
  defaultValue?: any;
  /** Column comment */
  comment?: string;
}

/**
 * Index schema
 * インデックススキーマ
 */
export interface IndexSchema {
  /** Index name */
  name: string;
  /** Table the index is on */
  tableName: string;
  /** Columns in the index */
  columns: string[];
  /** Whether it's a unique index */
  unique: boolean;
}

/**
 * KuzuDB data types
 * KuzuDBのデータ型
 */
export type KuzuDataType =
  | "BOOL"
  | "INT8"
  | "INT16"
  | "INT32"
  | "INT64"
  | "UINT8"
  | "UINT16"
  | "UINT32"
  | "UINT64"
  | "FLOAT"
  | "DOUBLE"
  | "STRING"
  | "DATE"
  | "TIMESTAMP"
  | "INTERVAL"
  | "LIST"
  | "STRUCT"
  | "MAP"
  | "UNION"
  | "NODE"
  | "REL";

// ========== DDL Parameter Types ==========

/**
 * Parameters for CREATE_NODE_TABLE operation
 * CREATE_NODE_TABLE操作のパラメータ
 */
export interface CreateNodeTableParams {
  tableName: string;
  columns: Array<{
    name: string;
    type: KuzuDataType;
    nullable?: boolean;
    defaultValue?: any;
  }>;
  primaryKey: string[];
  ifNotExists?: boolean;
}

/**
 * Parameters for CREATE_EDGE_TABLE operation
 * CREATE_EDGE_TABLE操作のパラメータ
 */
export interface CreateEdgeTableParams {
  tableName: string;
  fromTable: string;
  toTable: string;
  columns?: Array<{
    name: string;
    type: KuzuDataType;
    nullable?: boolean;
    defaultValue?: any;
  }>;
  ifNotExists?: boolean;
}

/**
 * Parameters for ADD_COLUMN operation
 * ADD_COLUMN操作のパラメータ
 */
export interface AddColumnParams {
  tableName: string;
  columnName: string;
  dataType: KuzuDataType;
  nullable?: boolean;
  defaultValue?: any;
  ifNotExists?: boolean;
}

/**
 * Parameters for DROP_COLUMN operation
 * DROP_COLUMN操作のパラメータ
 */
export interface DropColumnParams {
  tableName: string;
  columnName: string;
  ifExists?: boolean;
  cascade?: boolean;
}

/**
 * Parameters for RENAME_COLUMN operation
 * RENAME_COLUMN操作のパラメータ
 */
export interface RenameColumnParams {
  tableName: string;
  oldColumnName: string;
  newColumnName: string;
}

/**
 * Parameters for RENAME_TABLE operation
 * RENAME_TABLE操作のパラメータ
 */
export interface RenameTableParams {
  oldTableName: string;
  newTableName: string;
}

/**
 * Parameters for DROP_TABLE operation
 * DROP_TABLE操作のパラメータ
 */
export interface DropTableParams {
  tableName: string;
  ifExists?: boolean;
  cascade?: boolean;
}

/**
 * Parameters for CREATE_INDEX operation
 * CREATE_INDEX操作のパラメータ
 */
export interface CreateIndexParams {
  indexName: string;
  tableName: string;
  columns: string[];
  unique?: boolean;
  ifNotExists?: boolean;
}

/**
 * Parameters for DROP_INDEX operation
 * DROP_INDEX操作のパラメータ
 */
export interface DropIndexParams {
  indexName: string;
  ifExists?: boolean;
}

/**
 * Parameters for COMMENT operations
 * COMMENT操作のパラメータ
 */
export interface CommentParams {
  targetType: "TABLE" | "COLUMN";
  tableName: string;
  columnName?: string;
  comment: string | null;  // null to remove comment
}

// ========== DDL Event Impact Types ==========

/**
 * Extended EventImpact for DDL operations
 * DDL操作用の拡張EventImpact
 */
export type DDLEventImpact = EventImpact 
  | "CREATE_SCHEMA"
  | "ALTER_SCHEMA"
  | "DROP_SCHEMA"
  | "CREATE_INDEX"
  | "DROP_INDEX";

/**
 * DDL Template Metadata extending base metadata
 * ベースメタデータを拡張するDDLテンプレートメタデータ
 */
export interface DDLTemplateMetadata {
  requiredParams: string[];
  paramTypes?: Record<string, string>;
  impact: DDLEventImpact;
  validation?: Record<string, any>;
  /** Whether this DDL operation requires exclusive lock */
  requiresExclusiveLock?: boolean;
  /** Estimated duration for the operation */
  estimatedDuration?: number;
}

// ========== Utility Types ==========

/**
 * Type guard to check if event is DDL
 * イベントがDDLかどうかをチェックする型ガード
 */
export function isDDLEvent(event: TemplateEvent | DDLTemplateEvent): event is DDLTemplateEvent {
  return 'type' in event && event.type === 'DDL';
}

/**
 * Type guard to check if operation modifies schema structure
 * 操作がスキーマ構造を変更するかどうかをチェックする型ガード
 */
export function isSchemaModifyingOperation(ddlType: DDLOperationType): boolean {
  const modifyingOps: DDLOperationType[] = [
    "CREATE_NODE_TABLE",
    "CREATE_TABLE",
    "DROP_NODE_TABLE",
    "DROP_TABLE",
    "CREATE_EDGE_TABLE",
    "DROP_EDGE_TABLE",
    "ADD_COLUMN",
    "ALTER_TABLE_ADD_COLUMN",
    "DROP_COLUMN",
    "ALTER_TABLE_DROP_COLUMN",
    "RENAME_COLUMN",
    "ALTER_COLUMN_TYPE",
    "RENAME_TABLE"
  ];
  return modifyingOps.includes(ddlType);
}

/**
 * Schema migration event
 * スキーママイグレーションイベント
 */
export interface SchemaMigrationEvent extends DDLTemplateEvent {
  /** Migration version */
  migrationVersion: string;
  /** Migration description */
  description: string;
  /** Whether this migration is reversible */
  reversible: boolean;
  /** Rollback DDL if reversible */
  rollbackDDL?: string;
}