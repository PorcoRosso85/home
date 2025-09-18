/**
 * Event Sourcing Types
 * イベントソーシングの型定義
 */

// ========== Event Types ==========

export type TemplateEvent = {
  id: string;
  template: string;
  params: Record<string, any>;
  timestamp: number;
  clientId?: string;
  checksum?: string;
};

export type StoredEvent = TemplateEvent & {
  position: number;
};

export type EventImpact = "CREATE_NODE" | "UPDATE_NODE" | "DELETE_NODE" | "CREATE_EDGE" | "UPDATE_EDGE" | "DELETE_EDGE" | "LOGICAL_DELETE";

export type TemplateMetadata = {
  requiredParams: string[];
  paramTypes?: Record<string, string>;
  impact: EventImpact;
  validation?: Record<string, any>;
};

// ========== Store Types ==========

export type ServerSnapshot = {
  events: StoredEvent[];
  timestamp: number;
  position: number;
};

export type Impact = {
  addedNodes: number;
  addedEdges: number;
  deletedNodes: number;
  deletedEdges?: number;
  edgeType?: string;
  warning?: string;
};

export type Conflict = {
  type: string;
  events: TemplateEvent[];
};

// ========== Function Types ==========

export type ConflictResolver = (a: TemplateEvent, b: TemplateEvent) => TemplateEvent;

export type EventFilter = (event: TemplateEvent) => boolean;

export type EventHandler = (event: TemplateEvent) => void | Promise<void>;

// ========== Transaction Types ==========

export type EventGroupStatus = 'pending' | 'committed' | 'rolled_back';

export type EventGroup = {
  id: string;
  events: TemplateEvent[];
  timestamp: number;
  status: EventGroupStatus;
};