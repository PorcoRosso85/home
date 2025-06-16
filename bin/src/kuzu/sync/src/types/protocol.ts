/**
 * KuzuDB Realtime Sync Protocol Types
 * Based on Matthew Weidner's ID-based operations approach
 */

// Base patch structure
export interface BasePatch {
  id: string;           // Patch UUID
  timestamp: number;    // Client timestamp (Unix ms)
  clientId: string;     // Client identifier
  baseVersion?: number; // Base version for optimistic updates
}

// Node operations
export interface NodePatch extends BasePatch {
  op: 'create_node' | 'update_node' | 'delete_node';
  nodeId: string;       // Node UUID
  data?: {
    label?: string;
    properties?: Record<string, any>;
  };
}

// Edge operations
export interface EdgePatch extends BasePatch {
  op: 'create_edge' | 'update_edge' | 'delete_edge';
  edgeId: string;       // Edge UUID
  data?: {
    label?: string;
    fromNodeId?: string;
    toNodeId?: string;
    properties?: Record<string, any>;
  };
}

// Property operations
export interface PropertyPatch extends BasePatch {
  op: 'set_property' | 'remove_property';
  targetType: 'node' | 'edge';
  targetId: string;
  propertyKey: string;
  propertyValue?: any;  // Not needed for remove_property
}

// Union type for all patches
export type GraphPatch = NodePatch | EdgePatch | PropertyPatch;

// Server response types
export interface PatchResponse {
  patchId: string;
  status: 'accepted' | 'rejected' | 'ignored';
  reason?: string;
  serverVersion: number;
}

export interface SyncState {
  version: number;
  patches: GraphPatch[];
  snapshot?: {
    timestamp: number;
    url: string;  // R2 URL for snapshot
  };
}

// WebSocket message types
export interface ClientMessage {
  type: 'patch' | 'sync_request' | 'heartbeat';
  payload: GraphPatch | { fromVersion: number } | null;
}

export interface ServerMessage {
  type: 'patch_broadcast' | 'patch_response' | 'sync_state' | 'error';
  payload: GraphPatch | PatchResponse | SyncState | { message: string };
}

// ID generation helpers
export type EntityType = 'node' | 'edge' | 'patch';

export function generateId(type: EntityType): string {
  const uuid = crypto.randomUUID();
  const prefix = {
    'node': 'n',
    'edge': 'e',
    'patch': 'p'
  }[type];
  return `${prefix}_${uuid}`;
}

// Type guards
export function isNodePatch(patch: GraphPatch): patch is NodePatch {
  return patch.op.includes('node');
}

export function isEdgePatch(patch: GraphPatch): patch is EdgePatch {
  return patch.op.includes('edge');
}

export function isPropertyPatch(patch: GraphPatch): patch is PropertyPatch {
  return patch.op === 'set_property' || patch.op === 'remove_property';
}