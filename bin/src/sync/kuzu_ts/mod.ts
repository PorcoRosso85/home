/**
 * Unified Sync Module
 * 統合同期モジュールの公開API
 */

// Re-export all types
export type {
  KuzuWasmClient,
  LocalState,
  WebSocketSync,
  WebSocketMessage,
  ServerEventStore,
  EventSnapshot,
  ConflictResolver,
  ConflictResolution,
  MetricsCollector,
  MetricsStats
} from "./types.ts";

// Re-export implementations
export { KuzuWasmClientImpl } from "./core/client/kuzu_wasm_client.ts";
export { KuzuTsClientImpl } from "./core/client/kuzu_ts_client.ts";
export { WebSocketSyncImpl } from "./core/websocket/sync.ts";
export { TransactionalSyncAdapter } from "./core/sync/transactional_sync_adapter.ts";
export { ServerEventStoreImpl } from "./storage/server_event_store.ts";
export { CompressedEventStore } from "./storage/compressed_event_store.ts";
export { ConflictResolverImpl } from "./core/sync/conflict_resolver.ts";
export { MetricsCollectorImpl } from "./operations/metrics_collector.ts";
export { SyncKuzuClient, type SyncKuzuClientOptions } from "./core/sync_kuzu_client.ts";

// Re-export event sourcing components
export { 
  TemplateEventFactory, 
  TemplateRegistry, 
  TemplateEventStore,
  TemplateValidator,
  ImpactPredictor
} from "./event_sourcing/template_event_store.ts";

// Re-export GDPR deletion handler
export { 
  LogicalDeleteHandler,
  type LogicalDeleteEvent,
  type DeletionInfo,
  type DeletionResult
} from "./event_sourcing/delete_templates.ts";

// Re-export distributed components
export { 
  VectorClock,
  type ClockSnapshot
} from "./distributed/vector_clock.ts";

// Re-export transaction components
export { KuzuTransactionManager } from "./transaction/kuzu_transaction_manager.ts";
export { 
  type Transaction,
  type TransactionManager,
  type TransactionContext,
  type TransactionOptions,
  type TransactionResult,
  type TransactionStatus,
  TransactionError,
  TransactionErrorCode
} from "./transaction/types.ts";

// Re-export event group components
export {
  EventGroupManager
} from "./event_sourcing/event_group_manager.ts";

// Re-export event sourcing types
export type {
  TemplateEvent,
  EventGroup,
  EventGroupStatus
} from "./event_sourcing/types.ts";

// Re-export cache components
export { StateCache } from "./core/cache/state_cache.ts";
export { 
  AggregateCache,
  type AggregateType,
  type AggregateDefinition,
  type AggregateStats,
  type AggregateMemoryStats
} from "./core/cache/aggregate_cache.ts";

// ServerKuzuClient has been deprecated and removed

// Re-export DDL components
export {
  DDLTemplateRegistry,
  buildDDLQuery,
  validateDDLParams,
  generateCreateNodeTableQuery,
  generateCreateEdgeTableQuery,
  generateAddColumnQuery,
  generateDropColumnQuery,
  generateRenameColumnQuery,
  generateRenameTableQuery,
  generateDropTableQuery,
  generateCreateIndexQuery,
  generateDropIndexQuery,
  generateCommentQuery,
  validateTableName,
  validateColumnName,
  validateDataType
} from "./event_sourcing/ddl_templates.ts";

export {
  DDLEventHandler,
  ExtendedTemplateRegistry,
  createUnifiedEvent
} from "./event_sourcing/ddl_event_handler.ts";

// Re-export DDL types
export type {
  DDLTemplateEvent,
  DDLPayload,
  DDLOperationType,
  DDLMetadata,
  DDLTemplateMetadata,
  SchemaVersion,
  SchemaState,
  NodeTableSchema,
  EdgeTableSchema,
  ColumnSchema,
  IndexSchema,
  KuzuDataType,
  CreateNodeTableParams,
  CreateEdgeTableParams,
  AddColumnParams,
  DropColumnParams,
  RenameColumnParams,
  RenameTableParams,
  DropTableParams,
  CreateIndexParams,
  DropIndexParams,
  CommentParams,
  DDLEventImpact,
  SchemaMigrationEvent
} from "./event_sourcing/ddl_types.ts";

export {
  isDDLEvent,
  isSchemaModifyingOperation
} from "./event_sourcing/ddl_types.ts";

// Re-export SchemaManager
export { 
  SchemaManager,
  createSchemaManager,
  type SchemaSyncState,
  type SchemaConflict
} from "./core/schema_manager.ts";

// Re-export telemetry wrapper
export {
  createTelemetryWrapper,
  type TelemetryWrapper
} from "./telemetry_wrapper.ts";

// Re-export runtime-specific clients
export { KuzuSyncClient as DenoKuzuSyncClient } from "./deno_client.ts";
export { KuzuSyncClient as BunKuzuSyncClient } from "./bun_client.ts";

// Re-export unified client interface
export {
  createSyncClient,
  type ISyncClient,
  type SyncClientOptions,
  type SyncEvent,
  Result,
  tryCatch
} from "./unified_client.ts";