/**
 * Event Sourcing Module
 * イベントソーシングモジュールの公開API
 */

// Re-export all types
export type {
  TemplateEvent,
  StoredEvent,
  EventImpact,
  TemplateMetadata,
  ServerSnapshot,
  Impact,
  Conflict,
  ConflictResolver,
  EventFilter,
  EventHandler
} from "./types.ts";

// Re-export core functions
export {
  generateEventId,
  createTemplateEvent,
  calculateChecksum,
  validateParams,
  predictImpact,
  detectConflicts,
  filterEventsSince,
  getLatestEvents,
  validateChecksum
} from "./core.ts";

// Re-export classes from implementation files
export {
  TemplateLoader,
  TemplateRegistry,
  TemplateValidator,
  TemplateEventFactory,
  ParamValidator,
  TemplateEventStore,
  SnapshotableEventStore,
  ImpactPredictor,
  EventBroadcaster,
  EventReceiver,
  ConcurrentEventHandler,
  SecureTemplateExecutor,
  ChecksumValidator
} from "./template_event_store.ts";

export {
  KuzuEventClient
} from "./kuzu_client_real.ts";