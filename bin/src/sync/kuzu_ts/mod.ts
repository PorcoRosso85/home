/**
 * Unified Sync Module
 * 統合同期モジュールの公開API
 */

// Re-export all types
export type {
  BrowserKuzuClient,
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
export { BrowserKuzuClientImpl } from "./core/client/browser_kuzu_client.ts";
export { WebSocketSyncImpl } from "./core/websocket/sync.ts";
export { ServerEventStoreImpl } from "./storage/server_event_store.ts";
export { CompressedEventStore } from "./storage/compressed_event_store.ts";
export { ConflictResolverImpl } from "./core/sync/conflict_resolver.ts";
export { MetricsCollectorImpl } from "./operations/metrics_collector.ts";

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